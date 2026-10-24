# imports
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from lark import Lark, LarkError, Token, Tree

DEFAULT_GRAMMAR = Path(__file__).parent / "settings" / "grammar.txt"

# DATACLASS

@dataclass
class Product:
    name: str
    price: float
    stock: int

products: dict[str, Product] = {
    "monorail": Product(name="Monorail", price=1449.99, stock=30),
    "hewlett_packard": Product(name="Hewlett Packard", price=1849.99, stock=23),
    "compaq": Product(name="COMPAQ", price=2399.99, stock=8),
}

# CONFIG

@dataclass
class Config:
    grammar_file: Path

    @staticmethod
    def from_args() -> Config:
        prsr = argparse.ArgumentParser(description=__doc__)
        prsr.add_argument("-g", "--grammar", type=Path, default=DEFAULT_GRAMMAR, help="Lark grammar file")

        args = prsr.parse_args()
        return Config(grammar_file=args.grammar)

cfg = Config.from_args()


# NLP

def pretty_print(node: Tree|Token, depth: int=0) -> None:
    if isinstance(node, Token):
        print(" "*depth + f"{node.type} = {node}")
        return
    print(" "*depth + node.data)
    for subtree in node.children:
        pretty_print(subtree, depth+1)


def process_query(parser: Lark, query: str) -> str:
    try:
        tree = parser.parse(query)
    except LarkError as e:
        return f"Could not parse the query: \n{e}"

    query_node = tree.children[0]
    if not isinstance(query_node, Tree):
        return "Unable to process query."

    item = next(query_node.find_token("ITEM"), None)
    if item is None:
        return "Unable to process query."

    name = str(item).lower()
    product = products.get(name) or products.get(name.rstrip("s"))

    if product is None:
        return f"Unknown product: {item}"

    if query_node.data == "price_question":
        return f"The {product.name} costs {product.price:.2f}$"

    if query_node.data == "stock_question":
        if product.stock > 0:
            return f"Yes, {product.stock} in stock."
        return f"No, {product.name} is out of stock."

    if query_node.data == "count_question":
        return f"{product.stock} {product.name} in stock."
    return "Unable to process query."



# MAIN


def main() -> None:
    cfg = Config.from_args()

    try:
        parser = Lark.open(str(cfg.grammar_file), parser="earley")
    except (OSError, UnicodeDecodeError, LarkError) as e:
        print(f"Cannot load grammar {cfg.grammar_file}: {e}")
        sys.exit(1)

    while True:
        try:
            query = input("Query : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if query.upper() == "END":
            break
        print(process_query(parser, query))



if __name__ == "__main__":
    main()
