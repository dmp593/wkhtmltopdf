import subprocess
import requests

from functools import cache

from pathlib import Path

from app.utils import make_tmpfile


WKHTMLTOPDF_BINARY_PATH = "wkhtmltopdf"


@cache
def help(mode: str = None) -> bytes:
    match mode:
        case "html":
            help_option = "--htmldoc"
        case "extended":
            help_option = "--extended-help"
        case _: # help output is the default (simple)
            help_option = "--help"
    
    return subprocess.check_output([WKHTMLTOPDF_BINARY_PATH, help_option])


def generate_pdf(html_filepath: Path | str, options: dict[str, str], pdf_filepath: Path | str | None = None) -> Path:
    html_filepath = Path(html_filepath)
    pdf_filepath = Path(pdf_filepath) if pdf_filepath else make_tmpfile(suffix="pdf", touch=False)
    
    if not html_filepath.exists():
        raise Exception("Path to the HTML file does not exist!")

    # cmd_args = ["/usr/bin/xvfb-run", WKHTMLTOPDF_BINARY_PATH]
    cmd_args = [WKHTMLTOPDF_BINARY_PATH]

    for key, value in options.items():
        cmd_args.append(f"--{key}")

        if key in ["header-html", "footer-html"]:
            filepath = make_tmpfile(suffix=".html")
            filepath.write_bytes(requests.get(value).content)
            value = filepath

        if value:
            cmd_args.append(value)
        
    cmd_args.append(html_filepath)
    cmd_args.append(pdf_filepath)

    subprocess.run(cmd_args)

    return pdf_filepath
