import 'package:flutter/material.dart';

import '../../core/models/payment_models.dart';
import '../../core/utils/money.dart';

class SessionDetailScreen extends StatelessWidget {
  const SessionDetailScreen({
    super.key,
    required this.session,
  });

  final PaymentSession session;

  @override
  Widget build(BuildContext context) {
    final totals = session.personTotals();
    return Scaffold(
      appBar: AppBar(
        title: Text(_formatDate(session.date)),
      ),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 900;
          final content = _SessionDetail(
            session: session,
            totals: totals,
          );
          return Center(
            child: ConstrainedBox(
              constraints: BoxConstraints(
                maxWidth: wide ? 980 : 680,
              ),
              child: content,
            ),
          );
        },
      ),
    );
  }
}

class _SessionDetail extends StatelessWidget {
  const _SessionDetail({
    required this.session,
    required this.totals,
  });

  final PaymentSession session;
  final Map<String, int> totals;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 20, 16, 40),
      children: [
        if (session.category.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Chip(label: Text(session.category)),
          ),
        if (session.note.isNotEmpty)
          Text(
            session.note,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        const SizedBox(height: 16),
        Card(
          color: Theme.of(context).colorScheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Session total',
                      style: Theme.of(context).textTheme.labelLarge,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      session.totalLabel,
                      style:
                          Theme.of(context).textTheme.headlineMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                              ),
                    ),
                  ],
                ),
                Text(
                  '${session.receipts.length} '
                  '${session.receipts.length == 1 ? 'store' : 'stores'}',
                  style: Theme.of(context).textTheme.labelLarge,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'People',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 10),
        Card(
          child: Column(
            children: [
              for (var index = 0; index < session.people.length; index++) ...[
                ListTile(
                  leading: CircleAvatar(
                    child: Text(
                      session.people[index].name.characters.first.toUpperCase(),
                    ),
                  ),
                  title: Text(session.people[index].name),
                  trailing: Text(
                    Money.formatSigned(totals[session.people[index].name] ?? 0),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                          color: _balanceColor(
                            context,
                            totals[session.people[index].name] ?? 0,
                          ),
                        ),
                  ),
                ),
                if (index != session.people.length - 1)
                  const Divider(height: 1),
              ],
            ],
          ),
        ),
        const SizedBox(height: 20),
        Text(
          'Stores',
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: 10),
        for (final receipt in session.receipts) ...[
          _StoreCard(receipt: receipt),
          const SizedBox(height: 12),
        ],
      ],
    );
  }

  Color _balanceColor(BuildContext context, int cents) {
    final colors = Theme.of(context).colorScheme;
    if (cents > 0) {
      return colors.primary;
    }
    if (cents < 0) {
      return colors.error;
    }
    return colors.outline;
  }
}

class _StoreCard extends StatelessWidget {
  const _StoreCard({required this.receipt});

  final StoreReceipt receipt;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    receipt.storeName,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                ),
                Text(
                  receipt.totalLabel,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              'Paid by ${receipt.payer?.name ?? 'unknown'}',
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.outline,
                  ),
            ),
            if (receipt.category.isNotEmpty) ...[
              const SizedBox(height: 8),
              Chip(
                visualDensity: VisualDensity.compact,
                label: Text(receipt.category),
              ),
            ],
            if (receipt.note.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(receipt.note),
            ],
            const SizedBox(height: 12),
            const Divider(height: 1),
            for (final item in receipt.items) ...[
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${item.product.name} '
                            '× ${item.product.quantity}',
                            style: Theme.of(context).textTheme.titleSmall,
                          ),
                        ),
                        Text(
                          item.product.totalLabel,
                          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                                fontWeight: FontWeight.w700,
                              ),
                        ),
                      ],
                    ),
                    if (item.product.category.isNotEmpty ||
                        item.product.note.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      if (item.product.category.isNotEmpty)
                        Text(
                          item.product.category,
                          style: Theme.of(context).textTheme.labelMedium?.copyWith(
                                color: Theme.of(context).colorScheme.outline,
                              ),
                        ),
                      if (item.product.note.isNotEmpty)
                        Text(
                          item.product.note,
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                    ],
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        for (final entry in item.allocations.entries)
                          Chip(
                            visualDensity: VisualDensity.compact,
                            label: Text(
                              '${entry.key}: ${Money.format(entry.value)}',
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
            ],
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
