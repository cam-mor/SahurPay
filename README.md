# SahurPay

SahurPay is a small WIP terminal app for splitting receipts with friends or roomies.

Go to the store, enter what was bought, choose who is responsible for each product, and SahurPay will keep track of the receipt and who owes what. It can also handle multiple stores in one payment session.

This started as a personal project, so it is intentionally simple and terminal-first (Although a visual interface is planned for comfort). All local.

## Features

### People and sessions

- Enter any number of people and give each person a name.
- Start a payment session on the current date.
- Change a session date later using `YYYY-MM-DD` format.
- View all previously saved sessions.
- Delete a whole session with confirmation.
- Create one session that contains multiple store receipts.

### Products and receipts

- Enter a store name.
- Add products with:
  - Name
  - Quantity
  - Unit price
- Assign an optional category and note to the session.
- Assign an optional category and note to each store receipt.
- Assign an optional category and note to each product.
- Assign responsible people to each product.
- Split a product equally among one or more selected people.
- Calculate the exact receipt total and each person's share.
- Record who paid at each store, or leave the payer unknown.
- Use `Decimal` currency arithmetic and cent rounding so the totals stay predictable.
- Deterministically distribute an indivisible cent remainder across the selected people.

### Editing

The **Changes** menu lets you edit existing sessions and receipts:

- Session date
- Store name
- Store payer
- Product name
- Product quantity
- Product unit price
- Responsible people
- Session category
- Session note
- Store category
- Store note
- Product category
- Product note
- Delete an individual product
- Delete an entire store receipt

Edits automatically recalculate store, session, and per-person totals.

### Undo

- Undo the latest in-process session edit.
- Undo the latest session deletion.
- Undo session creation and backup import replacement.
- Keep up to 20 undo snapshots while the app is running.
- Persist every undo result immediately to the local JSON file.

Undo history is intentionally in-memory for now, so restarting the app clears it.

### Session history

- Search sessions by text, such as a store or product name.
- Filter by person.
- Filter by a date range.
- View sessions sorted with the newest date first.
- Display a session's stores, products, payer, totals, and allocations.

### Balances and settlements

- Calculate net balances across saved sessions.
- View who is owed money and who owes money.
- Suggest a deterministic list of transfers.
- Include receipts with a known payer in settlement calculations.

If the payer is unknown for a receipt, that receipt still contributes each person's share, but it cannot contribute to who should receive a payment.

### Backup and restore

- Export all saved sessions to a JSON backup file.
- Import and replace the current history from a JSON backup.
- Confirm before replacing saved sessions.
- Validate session IDs and backup structure before import.
- Save changes atomically so interrupted writes do not leave a partial session file.

### Safety and validation

- Reprompt for invalid dates, quantities, prices, selections, and menu choices.
- Require at least one person and at least one store per session.
- Require at least one responsible person and no duplicate responsible selections per product.
- Require unique person names within a session.
- Confirm destructive operations.
- Keep the local history out of Git with the repository `.gitignore`.

## Run it

SahurPay uses Python 3 and the standard library. No third-party package install is needed.

```bash
python3 main.py
```

The app starts with a simple menu:

```text
1. Log a new payment session
2. View saved sessions
3. Changes
4. Delete a session
5. Search sessions
6. View settlements
7. Backup and restore
8. Undo last change
9. Exit
```

## Example workflow

1. Choose **Log a new payment session**.
2. Enter the number of people and their names.
3. Enter a session date, or press Enter to use today's date.
4. Add a store.
5. Record who paid the store, or leave it blank if unknown.
6. Add products, quantities, unit prices, and responsible people.
7. Add another store or finish the store entry.
8. Finish the session entry.

The app prints:

- Store names and totals
- Product names and quantities
- Each product's per-person allocation
- The complete session total
- The amount owed or credited per person

## Example split

For a `$10.00` product shared by A, B, and C:

```text
A: $3.34
B: $3.33
C: $3.33
```

The `$0.01` remainder is assigned deterministically, and the three allocations add back to `$10.00`.

## Data storage

Saved sessions are stored locally at:

```text
data/sessions.json
```

The file is created automatically when the first session is saved. It is ignored by Git so personal payment history stays on the local machine.

For a portable copy, use **Backup and restore** in the app or copy the JSON file, if you know what you are doing.

## Project structure

```text
app.py         Domain classes and money/balance calculations
main.py        Terminal menu and interactive workflows
storage.py     JSON loading, saving, export, and import
test_app.py    Unit and smoke-test coverage
data/          Local saved payment history
```

## Tests

Run the test suite:

```bash
python3 -m unittest -v
```

Check Python syntax:

```bash
python3 -m py_compile app.py main.py storage.py test_app.py
```

## Roadmap

Possible future improvements:

- A graphical or web interface
- Payment status and marking a settlement as complete
- CSV export
- Recurring or duplicate sessions
- Currency selection and localization
- Session labels and product photos
