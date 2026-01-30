from __future__ import annotations

import argparse

from book_gen.config import load_config
from book_gen.db import Database
from book_gen.input_excel import import_books_from_excel
from book_gen.llm import LLMClient
from book_gen.notifications import Notifier
from book_gen.workflow_chapters import ChapterWorkflow
from book_gen.workflow_compile import CompileWorkflow
from book_gen.workflow_outline import OutlineWorkflow


def cmd_import_from_excel(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    db = Database(cfg)
    upserted = import_books_from_excel(db, args.excel_path)
    print(f"Imported/updated {len(upserted)} books from Excel.")


def cmd_generate_outlines(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    db = Database(cfg)
    llm = LLMClient(cfg)
    notifier = Notifier(cfg)
    wf = OutlineWorkflow(cfg, db, llm, notifier)
    wf.run()
    print("Outline generation workflow completed.")


def cmd_generate_chapters(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    db = Database(cfg)
    llm = LLMClient(cfg)
    notifier = Notifier(cfg)
    wf = ChapterWorkflow(cfg, db, llm, notifier)
    wf.run()
    print("Chapter generation workflow completed.")


def cmd_compile_books(args: argparse.Namespace) -> None:
    cfg = load_config(args.config)
    db = Database(cfg)
    notifier = Notifier(cfg)
    wf = CompileWorkflow(cfg, db, notifier)
    wf.run()
    print("Compilation workflow completed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automated Book Generation System")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML file")

    sub = parser.add_subparsers(dest="command", required=True)

    p_imp = sub.add_parser("import-from-excel", help="Import books from Excel into Supabase")
    p_imp.add_argument("--excel-path", required=True, help="Path to Excel file (.xlsx)")
    p_imp.set_defaults(func=cmd_import_from_excel)

    p_outline = sub.add_parser("generate-outlines", help="Generate outlines for books")
    p_outline.set_defaults(func=cmd_generate_outlines)

    p_ch = sub.add_parser("generate-chapters", help="Generate chapters for books")
    p_ch.set_defaults(func=cmd_generate_chapters)

    p_comp = sub.add_parser("compile-books", help="Compile final books into text/docx")
    p_comp.set_defaults(func=cmd_compile_books)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()