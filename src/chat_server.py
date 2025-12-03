from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt
import json

from .ocr_utils import ocr_file
from .extractor import extract_invoice_data
from .db import SessionLocal, Invoice, User, init_db
from .local_ai_agent import (
    extraer_datos_con_ia,
    refinar_datos_factura,
    responder_pregunta_sobre_factura,
)


init_db()

# Configuración JWT
SECRET_KEY = "tu-clave-secreta-cambiar-en-produccion"  # Cambiar en producción
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

security = HTTPBearer()


class ChatRequest(BaseModel):
    question: str
    raw_text: Optional[str] = None
    data_structured: Optional[Dict[str, Any]] = None


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


def hash_password(password: str) -> str:
    """Hashea una contraseña usando bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependencia para obtener el usuario actual desde el token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()
    if user is None:
        raise credentials_exception
    return user


class ChatResponse(BaseModel):
    answer: str


app = FastAPI(title="Intelli-Invoice Chat Server")

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8501",  # Streamlit default
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Registra un nuevo usuario"""
    db = SessionLocal()
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(User.username == req.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya existe"
            )
        
        # Crear nuevo usuario
        password_hash = hash_password(req.password)
        new_user = User(username=req.username, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        
        # Crear token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": req.username}, expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            username=req.username
        )
    finally:
        db.close()


@app.post("/api/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Inicia sesión y devuelve un token JWT"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nombre de usuario o contraseña incorrectos"
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            username=user.username
        )
    finally:
        db.close()


@app.get("/api/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtiene información del usuario actual"""
    return {"username": current_user.username, "id": current_user.id}


def get_user_invoice_history(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Obtiene las últimas facturas procesadas por el usuario para usar como contexto.
    Esto permite que el modelo 'aprenda' de facturas anteriores del mismo usuario.
    """
    db = SessionLocal()
    try:
        invoices = db.query(Invoice).filter(
            Invoice.user_id == user_id
        ).order_by(Invoice.created_at.desc()).limit(limit).all()
        
        history = []
        for inv in invoices:
            try:
                data = json.loads(inv.data_complete) if inv.data_complete else {}
            except:
                data = {}
            # Asegurar que el raw_text esté en los datos
            if inv.raw_text_ocr and 'raw_text' not in data:
                data['raw_text'] = inv.raw_text_ocr
            history.append({
                "invoice_number": inv.invoice_number,
                "supplier": inv.supplier,
                "date": inv.date,
                "data": data,
                "raw_text_ocr": inv.raw_text_ocr or "",
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
            })
        return history
    finally:
        db.close()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint que usa la IA local para responder preguntas sobre facturas.
    Puede responder sobre la factura actual procesada o sobre facturas anteriores del usuario.
    Requiere autenticación y conoce el usuario actual.
    """
    # Obtener historial de facturas del usuario para contexto
    historial = get_user_invoice_history(current_user.id, limit=5)
    
    # Determinar qué datos usar para el contexto
    if req.raw_text and req.data_structured:
        # Prioridad 1: Usar factura actual si está disponible
        raw_text = req.raw_text
        data_estructurada = req.data_structured
    elif historial and len(historial) > 0:
        # Prioridad 2: Si no hay factura actual, usar el historial
        # Construir un contexto combinado de las facturas más recientes
        textos_ocr = []
        datos_combinados = []
        for inv in historial[:3]:
            # Intentar obtener raw_text de diferentes lugares
            raw_txt = inv.get('raw_text_ocr') or inv.get('data', {}).get('raw_text') or ''
            if raw_txt:
                textos_ocr.append(f"Factura {inv.get('invoice_number', 'N/A')} ({inv.get('supplier', 'N/A')}):\n{raw_txt}")
            datos_combinados.append(inv.get('data', {}))
        
        raw_text = "\n\n---\n\n".join(textos_ocr) if textos_ocr else "Sin texto OCR disponible en el historial."
        data_estructurada = {
            "historial_facturas": datos_combinados,
            "total_facturas": len(historial),
            "mensaje": "El usuario está preguntando sobre sus facturas anteriores."
        }
    else:
        # No hay facturas disponibles
        return ChatResponse(
            answer="No tienes facturas procesadas aún. Por favor, sube y procesa una factura primero para poder hacer preguntas."
        )
    
    # Modificar la pregunta para incluir el contexto del usuario
    pregunta_con_usuario = f"[Usuario: {current_user.username}] {req.question}"
    
    answer = responder_pregunta_sobre_factura(
        raw_text=raw_text,
        data_estructurada=data_estructurada,
        pregunta=pregunta_con_usuario,
        historial_usuario=historial if historial else None,
    )
    return ChatResponse(answer=answer)


class ProcessInvoiceResponse(BaseModel):
    raw_text: str
    data_initial: Dict[str, Any]
    data_refined: Optional[Dict[str, Any]] = None
    saved_to_db: bool = False


@app.post("/api/process-invoice", response_model=ProcessInvoiceResponse)
async def process_invoice(
    file: UploadFile = File(...),
    refine: bool = True,
    save_db: bool = False,
    current_user: User = Depends(get_current_user),
):
    """
    Sube un archivo de factura, realiza OCR + extracción clásica,
    opcionalmente refinamiento con IA local y guardado en BD.
    """
    try:
        suffix = ""
        if "." in file.filename:
            suffix = "." + file.filename.rsplit(".", 1)[1].lower()
    except Exception:
        suffix = ""

    import tempfile, os

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar archivo temporal: {e}")

    try:
        # OCR
        raw_text = ocr_file(tmp_path)
        
        # Obtener historial de facturas del usuario para contexto
        historial = get_user_invoice_history(current_user.id, limit=5)
        
        # PRIMERO: Intentar extracción con IA (modelo analiza directamente el texto OCR + historial)
        data_from_ia: Optional[Dict[str, Any]] = None
        try:
            data_from_ia = extraer_datos_con_ia(raw_text, historial_usuario=historial if historial else None)
            print(f"✓ Datos extraídos con IA local (usando {len(historial)} facturas anteriores como contexto)")
        except Exception as e:
            print(f"⚠️ Error extrayendo con IA local: {e}")
            data_from_ia = None
        
        # FALLBACK: Extracción clásica (solo si la IA falló)
        data_initial = extract_invoice_data(raw_text)
        
        # Usar datos de IA si están disponibles, sino usar los clásicos
        data_refined: Optional[Dict[str, Any]] = data_from_ia if data_from_ia else None
        
        # Si refine=True y no tenemos datos de IA, intentar refinamiento adicional
        if refine and not data_refined:
            try:
                data_refined = refinar_datos_factura(raw_text, data_initial)
            except Exception as e:
                print(f"⚠️ Error refinando con IA local: {e}")
                data_refined = None

        # Guardar AUTOMÁTICAMENTE toda la información en BD (asociada al usuario)
        datos_para_guardar = data_refined or data_initial
        saved = False
        try:
            db = SessionLocal()
            invoice = Invoice(
                user_id=current_user.id,
                invoice_number=str(datos_para_guardar.get("invoice_number") or ""),
                supplier=str(datos_para_guardar.get("supplier") or ""),
                nit=str(datos_para_guardar.get("nit") or ""),
                date=str(datos_para_guardar.get("date") or ""),
                subtotal=str(datos_para_guardar.get("subtotal") or ""),
                tax=str(datos_para_guardar.get("tax") or ""),
                total=str(datos_para_guardar.get("total") or ""),
                data_complete=json.dumps(datos_para_guardar, ensure_ascii=False),
                raw_text_ocr=raw_text,
            )
            db.add(invoice)
            db.commit()
            saved = True
            db.close()
            print(f"✓ Factura guardada en BD para usuario {current_user.username}")
        except Exception as e:
            print(f"⚠️ Error guardando en BD: {e}")

        return ProcessInvoiceResponse(
            raw_text=raw_text,
            data_initial=data_initial,
            data_refined=data_refined,
            saved_to_db=saved,
        )
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Servir frontend estático (SPA) desde la carpeta frontend/
app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend",
)



