"""Autentikasi JWT sederhana berbasis peran: Petugas (lihat saja) vs Koordinator (semua akses)."""
import os
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Header

from database import users_col

JWT_ALGORITHM = 'HS256'
TOKEN_EXPIRE_HOURS = 12

# Akun tetap: Petugas (lihat saja) & Koordinator (semua akses: tambah/hapus/edit)
ACCOUNTS = [
    {'username': 'kalgen', 'password': 'kalgen', 'role': 'petugas'},
    {'username': 'raihan', 'password': 'rakhasivi123', 'role': 'koordinator'},
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _secret() -> str:
    return os.environ['JWT_SECRET']


def create_token(username: str, role: str, token_version: int = 0) -> str:
    payload = {
        'sub': username,
        'role': role,
        'tv': token_version,
        'exp': datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


async def seed_accounts():
    """Buat 2 akun tetap (Petugas & Koordinator) sekali saja bila belum ada.

    Tidak pernah menimpa password/role akun yang sudah ada, agar fitur Ganti
    Password tidak ter-reset setiap kali backend restart.
    """
    for acc in ACCOUNTS:
        existing = await users_col.find_one({'username': acc['username']})
        if not existing:
            await users_col.insert_one({
                'username': acc['username'],
                'password_hash': hash_password(acc['password']),
                'role': acc['role'],
                'token_version': 0,
                'created_at': datetime.now(timezone.utc).isoformat(),
            })


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Ambil user dari header Authorization: Bearer <token>. Wajib untuk semua endpoint data.

    Memvalidasi ulang ke database (bukan hanya isi token) sehingga akun yang sudah
    dihapus atau baru saja ganti password langsung ditolak, tanpa menunggu token expired.
    """
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Belum login. Silakan login terlebih dahulu.')
    token = authorization[7:]
    try:
        payload = jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, 'Sesi login berakhir. Silakan login kembali.')
    except jwt.InvalidTokenError:
        raise HTTPException(401, 'Token tidak valid.')
    doc = await users_col.find_one({'username': payload.get('sub')}, {'_id': 0})
    if not doc:
        raise HTTPException(401, 'Akun tidak ditemukan. Silakan login kembali.')
    if doc.get('token_version', 0) != payload.get('tv', 0):
        raise HTTPException(401, 'Sesi tidak berlaku lagi (password baru saja diubah). Silakan login kembali.')
    return {'username': doc['username'], 'role': doc['role']}


async def require_koordinator(user: dict = Depends(get_current_user)):
    """Wajib untuk semua aksi Tambah/Edit/Hapus — hanya peran Koordinator."""
    if user['role'] != 'koordinator':
        raise HTTPException(403, 'Aksi ini hanya dapat dilakukan oleh Koordinator.')
    return user
