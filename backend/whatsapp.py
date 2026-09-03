"""Notifikasi WhatsApp (Meta WhatsApp Cloud API) untuk daftar reagen Kritis & Waspada."""
import os
from urllib.parse import quote

import httpx

MAX_BODY = 4000


def config():
    return {
        'token': os.environ.get('WHATSAPP_ACCESS_TOKEN', '').strip(),
        'phone_id': os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '').strip(),
        'version': os.environ.get('WHATSAPP_API_VERSION', 'v25.0').strip(),
        'recipient': os.environ.get('WHATSAPP_RECIPIENT_NUMBER', '').strip(),
    }


def is_configured():
    c = config()
    return bool(c['token'] and c['phone_id'] and c['recipient'])


def _prf_note(r):
    """Tandai '(sudah PRF)' bila reagen ini sudah punya PRF pada periode berjalan."""
    return ' (sudah PRF)' if r.get('prf') else ''


def build_message(label, rows):
    crit = [r for r in rows if r['status'] == 'critical']
    warn = [r for r in rows if r['status'] == 'warning']
    lines = [f'*LabStock – Notifikasi Stok Reagen*', f'Periode: {label}', '']
    lines.append(f'*KRITIS ({len(crit)})*')
    lines += [f'- {r["nama_reagen"]}: sisa {_n(r["sisa_stock"])} / buffer {_n(r["buffer_stock"])}{_prf_note(r)}'
              for r in crit] or ['- (tidak ada)']
    lines.append('')
    lines.append(f'*WASPADA ({len(warn)})*')
    lines += [f'- {r["nama_reagen"]}: sisa {_n(r["sisa_stock"])} / buffer {_n(r["buffer_stock"])}{_prf_note(r)}'
              for r in warn] or ['- (tidak ada)']
    body = '\n'.join(lines)
    if len(body) > MAX_BODY:
        body = body[:MAX_BODY - 20] + '\n... (dipotong)'
    return body, len(crit), len(warn)


def _n(v):
    if v is None:
        return '-'
    return str(int(v)) if float(v).is_integer() else str(v)


def wa_me_link(body, recipient=None):
    num = (recipient or config()['recipient']).lstrip('+')
    return f'https://wa.me/{num}?text={quote(body)}'


async def send_text(body):
    """Kirim pesan teks. Return (ok, info). Fallback template hello_world bila teks ditolak."""
    c = config()
    url = f'https://graph.facebook.com/{c["version"]}/{c["phone_id"]}/messages'
    headers = {'Authorization': f'Bearer {c["token"]}', 'Content-Type': 'application/json'}
    payload = {
        'messaging_product': 'whatsapp', 'recipient_type': 'individual',
        'to': c['recipient'], 'type': 'text',
        'text': {'preview_url': False, 'body': body},
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
        res = await client.post(url, json=payload, headers=headers)
        if res.is_success:
            data = res.json()
            return True, {'mode': 'text', 'message_id': (data.get('messages') or [{}])[0].get('id')}
        err = _err(res)
        # Di luar jendela 24 jam Meta menolak teks bebas -> coba template bawaan
        tpl = {
            'messaging_product': 'whatsapp', 'to': c['recipient'], 'type': 'template',
            'template': {'name': 'hello_world', 'language': {'code': 'en_US'}},
        }
        res2 = await client.post(url, json=tpl, headers=headers)
        if res2.is_success:
            data = res2.json()
            return True, {'mode': 'template', 'message_id': (data.get('messages') or [{}])[0].get('id'),
                          'note': f'Pesan teks ditolak ({err}); template hello_world terkirim.'}
        return False, {'error': err, 'template_error': _err(res2), 'status': res.status_code}


def _err(res):
    try:
        return res.json().get('error', {}).get('message', res.text)
    except ValueError:
        return res.text
