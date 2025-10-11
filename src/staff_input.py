# src/staff_input.py
from lookup import search_parcel, insert_parcel

def menu():
    print("\n=== STAFF PARCEL MENU ===")
    print("1. Search parcel")
    print("2. Insert new parcel manually")
    print("3. Exit")
    choice = input("Select option (1-3): ").strip()
    return choice


def manual_add():
    provider = input("Enter provider (PostNord/DAO/UPS/DHL): ").strip()
    digits = input("Enter last 4 digits: ").strip()
    insert_parcel(provider, digits)


def manual_search():
    provider = input("Enter provider (PostNord/DAO/UPS/DHL): ").strip()
    digits = input("Enter last 4 digits: ").strip()
    results = search_parcel(provider, digits)
    if results:
        print(f"\n✅ Found {len(results)} result(s):")
        for r in results:
            print(f"  ID {r[0]} | {r[1]} | {r[2]} | Status: {r[3]} | Time: {r[4]}")
    else:
        print("\n⚠️  No parcel found.")


def run_menu():
    while True:
        choice = menu()
        if choice == "1":
            manual_search()
        elif choice == "2":
            manual_add()
        elif choice == "3":
            print("👋 Exiting staff menu.")
            break
        else:
            print("Invalid option, try again.")


if __name__ == "__main__":
    run_menu()
