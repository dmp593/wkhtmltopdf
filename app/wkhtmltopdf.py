import subprocess
import requests

from humps import kebabize
from functools import cache
from pathlib import Path

from app.utils import ensure_http_scheme, get_hash, make_tmpfile


WKHTMLTOPDF_BINARY_PATH = "wkhtmltopdf"


@cache
def help(mode: str = None) -> bytes:
    match mode:
        case "html":
            help_option = "--htmldoc"
        case "extended" | "verbose":
            help_option = "--extended-help"
        case _: # help output is the default (simple)
            help_option = "--help"
    
    return subprocess.check_output([WKHTMLTOPDF_BINARY_PATH, help_option])


def make_cli_options(**options) -> list[str]:
    cli_options = []

    for key, value in options.items():
        key = kebabize(key)

        if not key.startswith("-"):
            key = f"-{key}" if len(key) == 1 else f"--{key}"
        
        cli_options.append(key)

        if key in ["header-html", "footer-html"]:
            filepath = make_tmpfile(suffix=".html")
            value = ensure_http_scheme(value)
            filepath.write_bytes(requests.get(value).content)
            value = filepath

        if value:
            cli_options.append(value)

    return cli_options


def generate_url_to_pdf(url: str, options: dict[str, str]) -> Path:
    url = ensure_http_scheme(url, default_secure=True)

    filename = get_hash(url.encode('utf-8'))
    pdf_filepath = make_tmpfile(name=filename, suffix=".pdf", touch=False)
    
    subprocess.run([
            WKHTMLTOPDF_BINARY_PATH,
            *make_cli_options(**options),
            url,
            pdf_filepath
        ])

    return pdf_filepath


def generate_html_to_pdf(html_filepath: Path, pdf_filepath: Path, options: dict[str, str]) -> Path:
    subprocess.run([
        WKHTMLTOPDF_BINARY_PATH,
        *make_cli_options(**options),
        html_filepath,
        pdf_filepath
    ])

    return pdf_filepath
