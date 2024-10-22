from argparse import ArgumentParser
from banks.baridi import Baridi


def parse_arguments():
    parser = ArgumentParser(description="Baridi CLI")

    parser.add_argument('-t', '--transfer', action='store_true', help="Transfer operation")
    parser.add_argument('-a', '--amount', type=str, help="Transfer amount")
    parser.add_argument('-d', '--dest', type=str, help="Transfer destination (RIP)")
    parser.add_argument('-f', '--flexy', action='store_true', help="Flexy operation")
    parser.add_argument('-p', '--phone', type=str, help="Flexy destination (phone number)")

    args = parser.parse_args()

    if args.transfer:
        if args.amount is None:
            parser.error("--amount is required when --transfer is specified.")
        if args.dest is None:
            parser.error("--dest is required when --transfer is specified.")
    elif args.flexy:
        if args.amount is None:
            parser.error("--amount is required when --flexy is specified.")
        if args.phone is None:
            parser.error("--phone is required when --flexy is specified.")

    return args


def main():
    args = parse_arguments()
    baridi = Baridi()

    if baridi.login():
        print(baridi.accounts())

        if args.transfer:
            baridi.transfer(args.dest, args.amount)
        elif args.flexy:
            baridi.flexy(args.phone, args.amount)


if __name__ == "__main__":
    main()
