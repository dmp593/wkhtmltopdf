from pathlib import Path
from app import wkhtmltopdf

from app.utils import make_tmpfile, get_hash
from fastapi import FastAPI, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, Response
from starlette import status


app = FastAPI()


@app.get("/help")
def help(mode: str = None):
    usage = wkhtmltopdf.help(mode)
    return Response(usage, media_type="text/html" if mode == "html" else "text/plain")


@app.get("/")
def list_files():
    files = {}
    
    for f in Path("/tmp").glob("*"):
        if not f.is_file():
            continue
        
        id = f.stem

        if id not in files:
            files[id] = []

        files[id].append(f.suffix[1:])

    return files


@app.get("/{id}")
def get_file(id: str, disposition: str = "inline"):
    path: Path = Path(f"/tmp/{id}")

    if not path.suffix:
        path = path.with_suffix(".pdf")

    suffix = path.suffix

    disposition = disposition.lower()
    if disposition not in ["inline", "attachment"]:
        disposition = "inline"

    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path,
        content_disposition_type=disposition,
        filename=path.name,
        media_type="application/pdf" if suffix == ".pdf" else "text/html"
    )


@app.post("/")
async def generate_pdf(request: Request) -> FileResponse:
    form = dict(await request.form())

    upload_file: UploadFile = form.pop("file")
    data = await upload_file.read() # FIXME if large file

    sha256 = get_hash(data, "sha256")
    pdf_filepath = make_tmpfile(sha256, suffix=".pdf", touch=False)

    headers = { "X-ID": sha256 }
    response_status_code = status.HTTP_200_OK

    force_rewrite = form.pop("force", "no") in [True, "1", "y", "yes", "true"]

    if force_rewrite or not pdf_filepath.with_suffix(".html").exists():
        response_status_code = status.HTTP_201_CREATED

        html_filepath = make_tmpfile(sha256, suffix=".html")
        html_filepath.write_bytes(data)

        wkhtmltopdf.generate_pdf(html_filepath, options=dict(form.items()), pdf_filepath=pdf_filepath)

    return FileResponse(
        pdf_filepath,
        status_code=response_status_code,
        media_type="application/pdf",
        headers=headers,
        filename=Path(upload_file.filename).stem + ".pdf"
    )


@app.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_files():
    [f.unlink() for f in Path("/tmp").glob("*") if f.is_file()]


@app.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_files(id: str):
    [f.unlink() for f in Path("/tmp").glob(f"{id}.*") if f.is_file()]
