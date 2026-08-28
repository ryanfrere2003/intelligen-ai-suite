"""Main terminal interface for the IntelliGen email classification system."""

from ml.main import email_classifier_main


def display_menu() -> None:
    """Display the main application menu."""

    print()
    print("=" * 50)
    print("IntelliGen AI Demonstration")
    print("=" * 50)
    print()
    print("1. Email dual AI model classification system.")
    print("2. Web privacy and scraper tool.")
    print("3. Exit")
    print()


def main() -> None:
    """Run the main terminal interface."""

    while True:

        display_menu()

        choice = input("Select an option: ").strip()
        print("\n")

        if choice == "1":
            print("\n")
            print("=" * 50)
            print("Loading dual AI email classification system...")
            print("=" * 50)
            print("\n")

            email_classifier_main()

                    
        if choice == "2":
            print("\n")
            print("=" * 50)
            print("Loading web scraper privacy generative response tool...")
            print("=" * 50)
            print("\n")

        elif choice == "3":
            print("\n")
            print("=" * 50)
            print("Exiting application.")
            print("=" * 50)
            print("\n")

            break

        else:

            print("\nPlease enter 0, 1, 2 or 3.")


if __name__ == "__main__":
    main()