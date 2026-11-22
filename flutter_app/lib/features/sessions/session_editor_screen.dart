import 'package:flutter/material.dart';

import '../../core/models/payment_models.dart';
import '../../core/utils/money.dart';

class SessionEditorScreen extends StatefulWidget {
  const SessionEditorScreen({super.key});

  @override
  State<SessionEditorScreen> createState() => _SessionEditorScreenState();
}

class _SessionEditorScreenState extends State<SessionEditorScreen> {
  final _peopleController =
      TextEditingController(text: 'A, B, C');
  final _storeNameController = TextEditingController();
  final _storeCategoryController = TextEditingController();
  final _storeNoteController = TextEditingController();
  final _productNameController = TextEditingController();
  final _quantityController = TextEditingController(text: '1');
  final _priceController = TextEditingController();
  final _productCategoryController = TextEditingController();
  final _productNoteController = TextEditingController();

  DateTime _date = DateTime.now();
  final _sessionCategoryController = TextEditingController();
  final _sessionNoteController = TextEditingController();
  Person? _payer;
  final Set<String> _selectedParticipants = {};
  final List<ReceiptItem> _currentItems = [];
  final List<StoreReceipt> _stores = [];

  @override
  void dispose() {
    _peopleController.dispose();
    _storeNameController.dispose();
    _storeCategoryController.dispose();
    _storeNoteController.dispose();
    _productNameController.dispose();
    _quantityController.dispose();
    _priceController.dispose();
    _productCategoryController.dispose();
    _productNoteController.dispose();
    _sessionCategoryController.dispose();
    _sessionNoteController.dispose();
    super.dispose();
  }

  List<Person> get _people {
    final names = _peopleController.text
        .split(',')
        .map((name) => name.trim())
        .where((name) => name.isNotEmpty)
        .toSet()
        .toList();
    return names.map(Person.new).toList();
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  Future<void> _pickDate() async {
    final selected = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(const Duration(days: 3650)),
    );
    if (selected != null) {
      setState(() {
        _date = selected;
      });
    }
  }

  void _addProduct() {
    final name = _productNameController.text.trim();
    if (name.isEmpty) {
      _showError('Enter a product name.');
      return;
    }
    final quantity = int.tryParse(_quantityController.text.trim());
    if (quantity == null || quantity <= 0) {
      _showError('Quantity must be a whole number greater than zero.');
      return;
    }

    int unitPriceCents;
    try {
      unitPriceCents =
          Money.centsFromString(_priceController.text);
    } on FormatException catch (error) {
      _showError(error.message);
      return;
    }
    if (unitPriceCents < 0) {
      _showError('Price cannot be negative.');
      return;
    }

    final people = _people;
    final participants = people
        .where((person) => _selectedParticipants.contains(person.name))
        .toList();
    if (participants.isEmpty) {
      _showError('Choose at least one responsible person.');
      return;
    }

    setState(() {
      _currentItems.add(
        ReceiptItem(
          product: Product(
            name: name,
            quantity: quantity,
            unitPriceCents: unitPriceCents,
            category: _productCategoryController.text.trim(),
            note: _productNoteController.text.trim(),
          ),
          participants: participants,
        ),
      );
      _productNameController.clear();
      _quantityController.text = '1';
      _priceController.clear();
      _productCategoryController.clear();
      _productNoteController.clear();
      _selectedParticipants.clear();
    });
  }

  void _addStore() {
    final storeName = _storeNameController.text.trim();
    if (storeName.isEmpty) {
      _showError('Enter a store name.');
      return;
    }
    if (_currentItems.isEmpty) {
      _showError('Add at least one product to this store.');
      return;
    }

    final people = _people;
    if (people.isEmpty) {
      _showError('Enter at least one person.');
      return;
    }

    setState(() {
      _stores.add(
        StoreReceipt(
          storeName: storeName,
          people: people,
          payer: _payer,
          category: _storeCategoryController.text.trim(),
          note: _storeNoteController.text.trim(),
          items: List<ReceiptItem>.from(_currentItems),
        ),
      );
      _storeNameController.clear();
      _storeCategoryController.clear();
      _storeNoteController.clear();
      _payer = null;
      _currentItems.clear();
    });
  }

  void _saveSession() {
    final people = _people;
    if (people.isEmpty) {
      _showError('Enter at least one person.');
      return;
    }

    var stores = List<StoreReceipt>.from(_stores);
    if (_storeNameController.text.trim().isNotEmpty ||
        _currentItems.isNotEmpty) {
      if (_storeNameController.text.trim().isEmpty) {
        _showError('Enter a store name for the current store.');
        return;
      }
      if (_currentItems.isEmpty) {
        _showError('Add at least one product to the current store.');
        return;
      }
      stores = [
        ...stores,
        StoreReceipt(
          storeName: _storeNameController.text.trim(),
          people: people,
          payer: _payer,
          category: _storeCategoryController.text.trim(),
          note: _storeNoteController.text.trim(),
          items: List<ReceiptItem>.from(_currentItems),
        ),
      ];
    }
    if (stores.isEmpty) {
      _showError('Add at least one store.');
      return;
    }

    final session = PaymentSession(
      id: 'session-${DateTime.now().microsecondsSinceEpoch}',
      date: _date,
      people: people,
      receipts: stores,
      category: _sessionCategoryController.text.trim(),
      note: _sessionNoteController.text.trim(),
    );
    Navigator.of(context).pop(session);
  }

  @override
  Widget build(BuildContext context) {
    final people = _people;
    return Scaffold(
      appBar: AppBar(
        title: const Text('New payment session'),
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 900;
          return Center(
            child: ConstrainedBox(
              constraints: BoxConstraints(
                maxWidth: wide ? 980 : 680,
              ),
              child: ListView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 120),
                children: [
                  _SectionCard(
                    title: '1. People and date',
                    children: [
                      TextField(
                        key: const Key('people-field'),
                        controller: _peopleController,
                        decoration: const InputDecoration(
                          labelText: 'People',
                          hintText: 'A, B, C',
                          helperText: 'Separate names with commas',
                          border: OutlineInputBorder(),
                        ),
                        onChanged: (_) => setState(() {}),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: _pickDate,
                        icon: const Icon(Icons.calendar_month),
                        label: Text(_formatDate(_date)),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _sessionCategoryController,
                        decoration: const InputDecoration(
                          labelText: 'Session category',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _sessionNoteController,
                        minLines: 2,
                        maxLines: 4,
                        decoration: const InputDecoration(
                          labelText: 'Session note',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _SectionCard(
                    title: '2. Store',
                    children: [
                      TextField(
                        key: const Key('store-name-field'),
                        controller: _storeNameController,
                        decoration: const InputDecoration(
                          labelText: 'Store name',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<Person>(
                        initialValue: _payer,
                        decoration: const InputDecoration(
                          labelText: 'Who paid',
                          border: OutlineInputBorder(),
                        ),
                        items: [
                          const DropdownMenuItem<Person>(
                            value: null,
                            child: Text('Unknown'),
                          ),
                          for (final person in people)
                            DropdownMenuItem<Person>(
                              value: person,
                              child: Text(person.name),
                            ),
                        ],
                        onChanged: (value) {
                          setState(() {
                            _payer = value;
                          });
                        },
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _storeCategoryController,
                        decoration: const InputDecoration(
                          labelText: 'Store category',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _storeNoteController,
                        decoration: const InputDecoration(
                          labelText: 'Store note',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _SectionCard(
                    title: '3. Products',
                    children: [
                      TextField(
                        key: const Key('product-name-field'),
                        controller: _productNameController,
                        decoration: const InputDecoration(
                          labelText: 'Product name',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              key: const Key('quantity-field'),
                              controller: _quantityController,
                              keyboardType: TextInputType.number,
                              decoration: const InputDecoration(
                                labelText: 'Quantity',
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: TextField(
                              key: const Key('price-field'),
                              controller: _priceController,
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                decimal: true,
                              ),
                              decoration: const InputDecoration(
                                labelText: 'Unit price',
                                hintText: '12.50',
                                border: OutlineInputBorder(),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _productCategoryController,
                        decoration: const InputDecoration(
                          labelText: 'Product category',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _productNoteController,
                        decoration: const InputDecoration(
                          labelText: 'Product note',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Responsible people',
                        style: Theme.of(context).textTheme.titleSmall,
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final person in people)
                            FilterChip(
                              label: Text(person.name),
                              selected: _selectedParticipants
                                  .contains(person.name),
                              onSelected: (selected) {
                                setState(() {
                                  if (selected) {
                                    _selectedParticipants
                                        .add(person.name);
                                  } else {
                                    _selectedParticipants
                                        .remove(person.name);
                                  }
                                });
                              },
                            ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        key: const Key('add-product-button'),
                        onPressed: _addProduct,
                        icon: const Icon(Icons.add),
                        label: const Text('Add product'),
                      ),
                      if (_currentItems.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        for (var index = 0;
                            index < _currentItems.length;
                            index++) ...[
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(
                              _currentItems[index].product.name,
                            ),
                            subtitle: Text(
                              '${_currentItems[index].product.quantity} × '
                              '${Money.format(_currentItems[index].product.unitPriceCents)}',
                            ),
                            trailing: IconButton(
                              tooltip: 'Remove product',
                              onPressed: () {
                                setState(() {
                                  _currentItems.removeAt(index);
                                });
                              },
                              icon: const Icon(Icons.delete_outline),
                            ),
                          ),
                        ],
                      ],
                      const SizedBox(height: 12),
                      FilledButton.icon(
                        key: const Key('add-store-button'),
                        onPressed: _addStore,
                        icon: const Icon(Icons.store),
                        label: const Text('Add store'),
                      ),
                    ],
                  ),
                  if (_stores.isNotEmpty) ...[
                    const SizedBox(height: 16),
                    _SectionCard(
                      title: 'Added stores',
                      children: [
                        for (var index = 0;
                            index < _stores.length;
                            index++) ...[
                          ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading: const Icon(Icons.storefront),
                            title: Text(_stores[index].storeName),
                            subtitle: Text(
                              '${_stores[index].items.length} '
                              '${_stores[index].items.length == 1 ? 'product' : 'products'} '
                              '· ${_stores[index].totalLabel}',
                            ),
                            trailing: IconButton(
                              tooltip: 'Remove store',
                              onPressed: () {
                                setState(() {
                                  _stores.removeAt(index);
                                });
                              },
                              icon: const Icon(Icons.delete_outline),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ],
              ),
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        key: const Key('save-session-button'),
        onPressed: _saveSession,
        icon: const Icon(Icons.check),
        label: const Text('Save session'),
      ),
    );
  }
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({
    required this.title,
    required this.children,
  });

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 14),
            ...children,
          ],
        ),
      ),
    );
  }
}

String _formatDate(DateTime date) {
  const months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
  ];
  return '${months[date.month - 1]} ${date.day}, ${date.year}';
}
