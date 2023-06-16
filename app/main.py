import json
from pathlib import Path
from fastapi import FastAPI, Request, UploadFile
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, Response
from starlette import status

from app import wkhtmltopdf
from app.utils import make_tmpfile, get_hash

app = FastAPI()


@app.get("/help")
def help(mode: str = "html"):
    usage = wkhtmltopdf.help(mode)
    return Response(usage, media_type="text/html" if mode == "html" else "text/plain")


@app.get("/exported")
def get_files():
    files = {}
    
    for f in Path("/tmp").glob("*"):
        if not f.is_file():
            continue
        
        id = f.stem

        if id not in files:
            files[id] = []

        files[id].append(f.suffix[1:])

    return files


@app.get("/exported/{id}")
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


@app.get("/")
async def generate_pdf_from_url(request: Request) -> FileResponse:
    query_params = dict(request.query_params)
    url = query_params.pop('url')
    pdf_filepath = wkhtmltopdf.generate_url_to_pdf(url, options=query_params)
    
    return FileResponse(
        pdf_filepath,
        media_type="application/pdf",
        headers={ "X-ID": pdf_filepath.stem },
        filename=f"{pdf_filepath.stem}.pdf"
    )


@app.post("/")
async def generate_pdf_from_html_file(request: Request) -> FileResponse:
    form = dict(await request.form())
    upload_file: UploadFile = form.pop("file")
    
    file_data_bytes = await upload_file.read() # FIXME if large file
    options_bytes = json.dumps(form, sort_keys=True).encode('utf8')

    sha256_request = get_hash(file_data_bytes + options_bytes, "sha256")
    pdf_filepath = make_tmpfile(sha256_request, suffix=".pdf", touch=False)

    response_status_code = status.HTTP_200_OK

    already_generated = pdf_filepath.with_suffix(".html").exists()
    force_regenerate = form.pop("regenerate", "no") in [True, "1", "y", "yes", "true"]

    if force_regenerate or not already_generated:
        response_status_code = status.HTTP_201_CREATED

        html_filepath = make_tmpfile(sha256_request, suffix=".html")
        html_filepath.write_bytes(file_data_bytes)

        wkhtmltopdf.generate_html_to_pdf(html_filepath, pdf_filepath, options=form)

    return FileResponse(
        pdf_filepath,
        status_code=response_status_code,
        media_type="application/pdf",
        headers={ "X-ID": sha256_request },
        filename=Path(upload_file.filename).stem + ".pdf"
    )


@app.delete("/exported", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_files():
    [f.unlink() for f in Path("/tmp").glob("*") if f.is_file()]


@app.delete("/exported/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_files(id: str):
    [f.unlink() for f in Path("/tmp").glob(f"{id}.*") if f.is_file()]
