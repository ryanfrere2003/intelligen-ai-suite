"""Main terminal interface for the IntelliGen email classification system."""

from .data import initialize_training_data
from .model_comparison import perform_full_model_training_and_comparison_round
from .hil_corrections import corrective_actions


def email_display_menu() -> None:
    """Display the main application menu."""

    print()
    print("=" * 50)
    print("       IntelliGen AI Email Classifier")
    print("=" * 50)
    print()
    print("0. Initialize training data and database.")
    print("1. Train and compare models.")
    print("2. Human-in-the-loop corrections.")
    print("3. Exit")
    print()


def email_classifier_main() -> None:
    """Run the main terminal interface."""

    while True:

        email_display_menu()

        choice = input("Select an option: ").strip()
        print("\n")

        if choice == "0":
            print("\n")
            print("=" * 50)
            print("Starting database and mailbox import, ensure a mailbox file is in the data DIR...")
            print("=" * 50)
            print("\n")

            initialize_training_data()
                    
        if choice == "1":
            print("\n")
            print("=" * 50)
            print("Starting model training and comparison...")
            print("=" * 50)
            print("\n")

            perform_full_model_training_and_comparison_round()

        elif choice == "2":
            print("\n")
            print("=" * 50)
            print("Starting human-in-the-loop corrections...")
            print("=" * 50)
            print("\n")

            corrective_actions()

        elif choice == "3":
            print("\n")
            print("=" * 50)
            print("Exiting application.")
            print("=" * 50)
            print("\n")

            break

        else:

            print("\nPlease enter 0, 1, 2 or 3.")
