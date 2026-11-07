"""Start and seed the integrated application on the existing local database."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_ENV = ROOT.parent / "labsoft/backend/.env"
RUN = Path("/tmp/opencode/aprovaai-local")
ORIGIN = "http://localhost:3000"
SEED_PASSWORD = "Teste-local-123456"
SERVICES = {
    "identity": ("backend/services/identity", 18101),
    "learning": ("backend/services/learning", 18102),
    "catalog": ("backend/services/catalog", 18103),
    "subscription": ("backend/apps/SubscriptionService", 18104),
    "access": ("backend/apps/AccessService", 18105),
    "engagement": ("backend/services/engagement", 18106),
    "psp": ("backend/apps/MockPSPService", 18110),
    "payment": ("backend/apps/PaymentService", 18108),
    "checkout": ("backend/apps/CheckoutService", 18107),
}
SCHEMAS = ("identity", "learning", "catalog", "subscription", "engagement", "payment", "checkout")
def local_url():
    from sqlalchemy.engine import make_url

    if not ORIGINAL_ENV.is_file():
        raise RuntimeError(f"Credencial antiga não encontrada: {ORIGINAL_ENV}")
    settings = dict(line.strip().split("=", 1) for line in ORIGINAL_ENV.read_text().splitlines()
                    if "=" in line and not line.lstrip().startswith("#"))
    url = make_url(settings["DATABASE_URL"])
    if url.host not in {"localhost", "127.0.0.1", "::1"} or url.database != "aprovaai" or (url.port or 5432) != 5432:
        raise RuntimeError("Recusado: somente PostgreSQL local localhost:5432/aprovaai")
    return url


def schema_url(url, schema):
    return url.set(drivername="postgresql+psycopg", query={"options": f"-csearch_path={schema}"}).render_as_string(hide_password=False)


def save(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not path.read_text().startswith("# gerado por scripts/local.py\n"):
        raise RuntimeError(f"Arquivo não gerenciado; não vou sobrescrever: {path}")
    path.write_text("# gerado por scripts/local.py\n" + text)
    path.chmod(0o600)


def read_env(path):
    return dict(line.split("=", 1) for line in path.read_text().splitlines()
                if "=" in line and not line.lstrip().startswith("#"))


def setup():
    if state_file().exists():
        raise RuntimeError("Encerre os processos com down antes de executar setup")
    url = local_url()
    print("Destino confirmado: localhost:5432/aprovaai; schema public será mantido.", flush=True)
    clean_env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    for name, (directory, _) in SERVICES.items():
        if name == "psp":
            continue  # PaymentService's environment also has the mock PSP's dependencies.
        print("Instalando", name, flush=True)
        subprocess.run(["uv", "sync", "--locked"], cwd=ROOT / directory, env=clean_env, check=True)
    if not (ROOT / "frontend/node_modules").exists():
        subprocess.run(["npm", "ci"], cwd=ROOT / "frontend", check=True)

    identity_example = read_env(ROOT / SERVICES["identity"][0] / ".env.example")
    catalog_example = read_env(ROOT / SERVICES["catalog"][0] / ".env.example")
    internal_token = identity_example["INTERNAL_SERVICE_TOKEN"]
    if len(internal_token) < 16:
        raise RuntimeError("Configure a chave interna local nos .env.example")

    import psycopg
    from psycopg import sql

    with psycopg.connect(host=url.host, port=url.port or 5432, dbname=url.database,
                         user=url.username, password=url.password, connect_timeout=5) as db:
        if not db.execute("SELECT has_database_privilege(current_user, current_database(), 'CREATE')").fetchone()[0]:
            raise RuntimeError("O usuário do .env não pode criar schemas neste banco")
        for schema in SCHEMAS:
            owner = db.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname=%s", (schema,)).fetchone()
            if owner and owner[0] != url.username:
                raise RuntimeError(f"Schema {schema} pertence a outro usuário; nada será alterado nele")
            db.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
        db.commit()

    base = {
        "IDENTITY_URL": "http://127.0.0.1:18101", "LEARNING_URL": "http://127.0.0.1:18102",
        "CATALOG_URL": "http://127.0.0.1:18103", "SUBSCRIPTION_URL": "http://127.0.0.1:18104",
        "ACCESS_URL": "http://127.0.0.1:18105", "ENGAGEMENT_URL": "http://127.0.0.1:18106",
        "CHECKOUT_URL": "http://127.0.0.1:18107", "PAYMENT_URL": "http://127.0.0.1:18108",
        "PSP_URL": "http://127.0.0.1:18110", "FRONTEND_ORIGIN": ORIGIN,
    }
    by_service = {
        "identity": {"AA_FRONTEND_ORIGIN": ORIGIN, "AA_PUBLIC_APP_URL": ORIGIN,
                     "AA_PASSWORD_RESET_URL": ORIGIN + "/recuperar-acesso", "AA_COOKIE_SECURE": "false",
                     "AA_EMAIL_FLOWS_ENABLED": "false",
                     "AA_MEDIA_ROOT": str(ROOT / "backend/services/identity/private_uploads"),
                     "AA_JWT_PRIVATE_KEY_B64": identity_example["AA_JWT_PRIVATE_KEY_B64"]},
        "learning": {"LEARNING_DEMO_MODE": "false", "STORAGE_DIR": str(ROOT / "backend/services/learning/storage")},
        "catalog": {"CATALOG_DEMO_MODE": "false", "MEDIA_ROOT": str(ROOT / "backend/services/catalog/var/media"),
                    "MEDIA_SIGNING_KEY": catalog_example["MEDIA_SIGNING_KEY"]},
        "engagement": {"LEARNING_DEMO_MODE": "false"},
        "subscription": {},
        "payment": {"PAYMENT_SELF_URL": "http://127.0.0.1:18108"},
        "checkout": {},
        "psp": {},
        "access": {},
    }
    for name, (directory, _) in SERVICES.items():
        settings = {**base, "INTERNAL_SERVICE_TOKEN": internal_token, **by_service[name]}
        if name in SCHEMAS:
            settings["DATABASE_URL"] = schema_url(url, name)
        save(ROOT / directory / ".env", "".join(f"{key}={value}\n" for key, value in settings.items()))

    frontend = {"NEXT_PUBLIC_AUTH_ENABLED": "true", "NEXT_PUBLIC_EMAIL_FLOWS_ENABLED": "false",
                "BACKEND_URL": base["LEARNING_URL"], **base}
    save(ROOT / "frontend/.env.local", "".join(f"{key}={value}\n" for key, value in frontend.items()))
    for name in SCHEMAS:
        directory = ROOT / SERVICES[name][0]
        env = {**clean_env, **base, "INTERNAL_SERVICE_TOKEN": internal_token,
               **by_service[name], "DATABASE_URL": schema_url(url, name)}
        print("Migrando", name, flush=True)
        subprocess.run([str(directory / ".venv/bin/python"), "-m", "alembic", "upgrade", "head"],
                       cwd=directory, env=env, check=True)
        subprocess.run([str(directory / ".venv/bin/python"), "-m", "alembic", "check"],
                       cwd=directory, env=env, check=True)
    print("Preparado. Nenhuma tabela de public foi removida. Execute 'up' e depois 'seed'.")


def service_env(name):
    path = ROOT / SERVICES[name][0] / ".env"
    if not path.is_file():
        raise RuntimeError(f"Falta {path}; execute setup")
    return {**os.environ, **read_env(path)}


def proc_start(pid):
    try:
        return (Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()[19])
    except (FileNotFoundError, IndexError):
        return None


def owned(pid, started, directory):
    try:
        return proc_start(pid) == started and Path(f"/proc/{pid}/cwd").resolve() == directory.resolve()
    except (FileNotFoundError, PermissionError):
        return False


def state_file():
    return RUN / "processes.json"


def health(port, frontend=False):
    target = ORIGIN if frontend else f"http://127.0.0.1:{port}/api/health"
    try:
        with urlopen(target, timeout=2) as response:
            return response.status == 200
    except Exception:
        return False


def up():
    if state_file().exists():
        raise RuntimeError("Há um registro de processos; use status/down antes de subir novamente")
    RUN.mkdir(parents=True, exist_ok=True)
    targets = [(name, ROOT / directory, port) for name, (directory, port) in SERVICES.items()]
    targets.append(("frontend", ROOT / "frontend", 3000))
    if any(health(port, name == "frontend") for name, _, port in targets):
        raise RuntimeError("Uma das portas já responde. Confira os serviços antes de continuar")
    processes = {}
    try:
        for name, directory, port in targets:
            if name == "frontend":
                env = {**os.environ, **read_env(directory / ".env.local")}
                command = ["npm", "run", "dev", "--", "--hostname", "localhost", "--port", "3000"]
            else:
                env = service_env(name)
                python = ROOT / SERVICES["payment"][0] / ".venv/bin/python" if name == "psp" else directory / ".venv/bin/python"
                command = [str(python), "-m", "uvicorn", "app.main:app",
                           "--host", "127.0.0.1", "--port", str(port)]
            with (RUN / f"{name}.log").open("w") as log:
                process = subprocess.Popen(command, cwd=directory, env=env, stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True)
            processes[name] = {"pid": process.pid, "started": proc_start(process.pid), "directory": str(directory), "port": port}
            state_file().write_text(json.dumps(processes))
            for _ in range(120):
                if process.poll() is not None:
                    raise RuntimeError(f"{name} encerrou; consulte {RUN / (name + '.log')}")
                if health(port, name == "frontend"):
                    print(f"{name}: http://{'localhost' if name == 'frontend' else '127.0.0.1'}:{port}", flush=True)
                    break
                time.sleep(.5)
            else:
                raise RuntimeError(f"{name} não respondeu; consulte {RUN / (name + '.log')}")
    except Exception:
        down()
        raise


def down():
    if not state_file().exists():
        print("Nenhum processo registrado")
        return
    processes = json.loads(state_file().read_text())
    for name, record in reversed(list(processes.items())):
        pid = record["pid"]
        if owned(pid, record["started"], Path(record["directory"])):
            os.killpg(pid, signal.SIGTERM)
            print("Encerrado:", name)
    state_file().unlink()


def status():
    if not state_file().exists():
        print("Nenhum processo registrado")
        return
    for name, record in json.loads(state_file().read_text()).items():
        alive = owned(record['pid'], record['started'], Path(record['directory']))
        print(f"{name}: {'ok' if alive and health(record['port'], name == 'frontend') else 'parado'}")


def reset():
    """Remove data from the local integration and legacy schemas; setup creates them again."""
    if state_file().exists():
        raise RuntimeError("Encerre os serviços com down antes do reset")
    url = local_url()
    if input("Apagar TODOS os dados de localhost:5432/aprovaai, inclusive public? Digite aprovaai: ") != "aprovaai":
        raise RuntimeError("Reset cancelado")

    import psycopg
    from psycopg import sql

    with psycopg.connect(host=url.host, port=url.port or 5432, dbname=url.database,
                         user=url.username, password=url.password, connect_timeout=5) as db:
        owns_database = db.execute("SELECT pg_get_userbyid(datdba)=current_user FROM pg_database WHERE datname=current_database()").fetchone()[0]
        if not owns_database:
            raise RuntimeError("O usuário do .env não é dono do banco; reset recusado")
        for schema in (*SCHEMAS, "public"):
            owner = db.execute("SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname=%s", (schema,)).fetchone()
            if owner and owner[0] not in {url.username, "pg_database_owner"}:
                raise RuntimeError(f"Schema {schema} pertence a outro usuário; reset recusado")
        for schema in (*SCHEMAS, "public"):
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
        db.execute("CREATE SCHEMA public")
        db.commit()
    print("Banco local vazio. Agora execute setup, up e seed, nessa ordem.")


def seed():
    import httpx
    from io import BytesIO
    from PIL import Image
    from reportlab.pdfgen import canvas
    from showcase import COURSES, TEACHERS, lessons_for

    identity = ROOT / SERVICES["identity"][0]
    tokens = json.loads(subprocess.check_output(
        [str(identity / ".venv/bin/python"), "-m", "app.seed_local", "--tokens"], cwd=identity,
        env={**service_env("identity"), "APROVAAI_LOCAL_SEED_PASSWORD": SEED_PASSWORD,
             "APROVAAI_LOCAL_TEACHERS": json.dumps(TEACHERS)}, text=True))
    print("Contas locais criadas/preservadas pela identidade.")

    video = RUN / "aula-local.mp4"
    if not video.exists():
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                        "-i", "testsrc=size=320x180:rate=24", "-t", "8", "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", str(video)], check=True)

    with httpx.Client(timeout=30, trust_env=False) as client:
        def request(service, method, path, headers=None, **kwargs):
            port = SERVICES[service][1]
            result = client.request(method, f"http://127.0.0.1:{port}{path}", headers=headers, **kwargs)
            result.raise_for_status()
            return result.json()

        student = {"Authorization": f"Bearer {tokens['aluno']}", "Origin": ORIGIN}
        plan_student = {"Authorization": f"Bearer {tokens['aluno-plano']}", "Origin": ORIGIN}
        free_course = free_lesson = None
        published_ids = []
        for key, title, owner, cover, subject, area, exams, summary, price, published, audience in COURSES:
            teacher = {"Authorization": f"Bearer {tokens[owner]}", "Origin": ORIGIN}
            listing = request("catalog", "GET", "/api/teacher/courses/summary?size=100", teacher)
            course = next((item for item in listing["items"] if item["title"] == title), None)
            cover_url = f"/images/courses/{cover}" if cover.endswith(".webp") else f"/{cover}"
            if course is None:
                course = request("catalog", "POST", "/api/courses", teacher, json={
                    "title": title, "subject": subject, "area": area, "summary": summary,
                    "audience": audience, "exams": exams,
                    "access_type": "paid" if price != "0.00" else "free", "price": price, "cover_url": cover_url,
                })
            course_id = course["id"]
            existing = request("learning", "GET", f"/api/learning/courses/{course_id}/lessons", teacher)
            by_position = {lesson["position"]: lesson for lesson in existing}
            first_lesson = None

            for position, (lesson_title, description, section) in enumerate(lessons_for(key), 1):
                lesson = by_position.get(position)
                if lesson is None:
                    lesson = request("learning", "POST", "/api/learning/lessons", teacher, json={
                        "course_id": course_id, "title": lesson_title, "description": description,
                        "section_title": section, "position": position,
                    })
                elif lesson["title"] != lesson_title:
                    raise RuntimeError(f"Aula {position} de {title} foi alterada; não vou sobrescrevê-la")
                if first_lesson is None:
                    first_lesson = lesson["id"]
                if not lesson["media_id"]:
                    with video.open("rb") as stream:
                        media = request("learning", "POST", "/api/media", teacher,
                                        files={"file": ("aula-local.mp4", stream, "video/mp4")})
                    request("learning", "PATCH", f"/api/learning/lessons/{lesson['id']}/media", teacher,
                            json={"media_id": media["id"]})
                if key == "fisica-enem-mecanica" and lesson_title == "Leis de Newton e suas aplicações" and not lesson["thumbnail_id"]:
                    source = ROOT / "frontend/public/images/video/leis-de-newton.webp"
                    output = BytesIO()
                    with Image.open(source) as image:
                        image.save(output, format="PNG")
                    thumbnail = request("learning", "POST", "/api/media/thumbnails", teacher,
                                        files={"file": ("leis-de-newton.png", output.getvalue(), "image/png")})
                    request("learning", "PATCH", f"/api/learning/lessons/{lesson['id']}/thumbnail", teacher,
                            json={"media_id": thumbnail["id"]})

            if key == "fisica-quantica":
                preview = request("catalog", "GET", f"/api/courses/{course_id}/preview", teacher)
                for material_title in ("Dualidade onda-partícula", "Lista de exercícios: modelos atômicos"):
                    if any(item["title"] == material_title for item in preview["materials"]):
                        continue
                    output = BytesIO()
                    pdf = canvas.Canvas(output)
                    pdf.drawString(64, 760, material_title)
                    pdf.save()
                    request("catalog", "POST", f"/api/courses/{course_id}/materials/upload", teacher,
                            data={"title": material_title, "kind": "PDF", "access_level": "enrolled"},
                            files={"file": ("material.pdf", output.getvalue(), "application/pdf")})

            if published and course["status"] != "published":
                request("catalog", "POST", f"/api/courses/{course_id}/publication", teacher,
                        json={"action": "publish"})
            if published:
                published_ids.append(course_id)
            if published and price == "0.00":
                request("subscription", "POST", "/api/subscriptions", student, json={"course_id": course_id})
            if key == "fisica-enem-mecanica":
                free_course, free_lesson = course_id, first_lesson
            print(f"{title}: {len(lessons_for(key))} aulas ({'publicado' if published else 'rascunho'})")

        question = "Como posso revisar o conteúdo desta primeira aula?"
        existing = request("engagement", "GET", "/api/questions/me", student)
        if not any(row["course_id"] == free_course and row["prompt"] == question for row in existing):
            request("engagement", "POST", "/api/questions", student,
                    json={"course_id": free_course, "lesson_id": free_lesson, "prompt": question})
        print("Engajamento: dúvida no curso gratuito de Mecânica.")

        subscription = request("subscription", "GET", "/api/subscriptions/me", plan_student)
        plan = subscription["complete_plan"]
        if plan is None:
            quote = request("checkout", "GET", "/api/checkout/quote?plan=monthly")
            if quote["amount_cents"] != 4990:
                raise RuntimeError("Preço do plano divergente; seed interrompido")
            key = f"seed-complete-plan-{subscription['user_id']}"
            checkout = request("checkout", "POST", "/api/checkout",
                               {**plan_student, "Idempotency-Key": key}, json={"plan": "monthly", "method": "pix"})
            deadline = time.monotonic() + 30
            while checkout["status"] == "processing" and time.monotonic() < deadline:
                time.sleep(.25)
                checkout = request("checkout", "GET", f"/api/checkout/{checkout['checkout_id']}", plan_student)
            if checkout["status"] != "ok":
                raise RuntimeError(f"Plano simulado não confirmado: {checkout['status']}")
        elif plan["status"] != "active" or plan["price"] != 4990:
            raise RuntimeError("Plano anterior está inativo ou divergente; seed não altera decisões do usuário")

        accessible = request("learning", "GET", "/api/learning/courses", plan_student)
        if {course["id"] for course in accessible} != set(published_ids):
            raise RuntimeError("Plano completo não liberou os sete cursos publicados")
        print("Aluno com plano completo: acesso aos sete cursos publicados pelo PSP simulado.")
    print("Contas locais: admin.local@exemplo.com, professor.local@exemplo.com,")
    print("aluno.local@exemplo.com e aluno-plano.local@exemplo.com")
    print(f"Senha compartilhada de teste: {SEED_PASSWORD}")
    print("Pagamento individual e assinatura: teste pelas telas; somente PSP simulado, sem cobrança real.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("setup", "up", "seed", "status", "down", "reset"))
    args = parser.parse_args()
    try:
        globals()[args.command]()
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
