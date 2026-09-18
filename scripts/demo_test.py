import urllib.request
import json
from pathlib import Path

def run():
    user = {
        'email': 'dr.chen@academic-hospital.org',
        'password': 'HospitalSecurePass2026!',
        'full_name': 'Dr. Sarah Chen, MD'
    }
    
    # Register or Login
    reg_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/auth/register',
        data=json.dumps(user).encode(),
        headers={'Content-Type': 'application/json'}
    )
    try:
        res = urllib.request.urlopen(reg_req)
        token = json.loads(res.read().decode())['data']['access_token']
    except Exception:
        login_req = urllib.request.Request(
            'http://127.0.0.1:8000/api/v1/auth/login',
            data=json.dumps({'email': user['email'], 'password': user['password']}).encode(),
            headers={'Content-Type': 'application/json'}
        )
        res = urllib.request.urlopen(login_req)
        token = json.loads(res.read().decode())['data']['access_token']

    print("[Auth] Access token verified")

    # Read image
    img_path = Path("datasets/test/xray/case_0031_brain.png")
    if not img_path.exists():
        img_path = Path("datasets/train/xray/case_0001_brain.png")
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    boundary = "----MedicalFormBoundaryXYZ123"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="file"; filename="case_0031_brain.png"\r\n')
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(img_bytes)
    body.extend(b"\r\n")
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(b'Content-Disposition: form-data; name="model_version"\r\n\r\n')
    body.extend(b"v1\r\n")
    body.extend(f"--{boundary}--\r\n".encode())

    post_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/inference",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
    )
    res = urllib.request.urlopen(post_req)
    data = json.loads(res.read().decode())['data']
    job_id = data['id']
    print(f"[Inference] Completed Job ID: {job_id}")
    print(f"[Inference] Processing time: {data['processing_time_ms']} ms")

    # Fetch slices
    slice_req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/v1/inference/{job_id}/slices",
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(slice_req)
    s_data = json.loads(res.read().decode())['data']
    print(f"[Volumetric PACS] Synthesized {s_data['total_slices']} slices across volume stack")

    print("\n" + "=" * 60)
    print("PROJECT IS RUNNING LIVE!")
    print(f"Direct Results Link: http://localhost:5173/result/{job_id}")
    print(f"Direct Clinical Report Link: http://localhost:5173/report/{job_id}")
    print(f"Main Application: http://localhost:5173")
    print(f"User Credentials: {user['email']} / {user['password']}")
    print("=" * 60)

if __name__ == "__main__":
    run()
