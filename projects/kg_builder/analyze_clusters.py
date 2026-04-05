import json
from collections import Counter, defaultdict

# Load data
with open('knowledge_graph_output/conversation_entities.json', 'r', encoding='utf-8') as f:
    conv_entities = json.load(f)

with open('knowledge_graph_output/entities.json', 'r', encoding='utf-8') as f:
    entities = json.load(f)

entity_map = {e['id']: e for e in entities}

# Build entity -> conversations map
entity_to_convs = defaultdict(set)
for conv_id, entity_list in conv_entities.items():
    for entity_id in entity_list:
        entity_to_convs[entity_id].add(conv_id)

print('CONVERSATION COMPLEXITY DISTRIBUTION')
print('=' * 70)

# Analyze conversation complexity
conv_sizes = {conv_id: len(set(eids)) for conv_id, eids in conv_entities.items()}
size_distribution = Counter(conv_sizes.values())

cumulative = 0
total = len(conv_sizes)
for size in sorted(size_distribution.keys())[:15]:
    count = size_distribution[size]
    pct = count / total * 100
    cumulative += count
    cum_pct = cumulative / total * 100
    bar = '#' * min(40, int(pct / 2))
    print(f'{size:2} entities: {count:5,} convos ({pct:5.1f}%) {bar} (cumulative: {cum_pct:5.1f}%)')

print()
print('STATISTICS:')
print('-' * 70)
avg_entities = sum(conv_sizes.values()) / len(conv_sizes)
max_conv = max(conv_sizes.items(), key=lambda x: x[1])
min_conv = min(conv_sizes.items(), key=lambda x: x[1])
print(f'  Average entities per conversation: {avg_entities:.1f}')
print(f'  Most complex conversation: {max_conv[1]} entities')
print(f'  Least complex: {min_conv[1]} entities')

print()
print('ENTITY AFFINITY CLUSTERS:')
print('=' * 70)

top_entity_ids = sorted(entity_to_convs.items(), key=lambda x: len(x[1]), reverse=True)[:10]

for eid, convs in top_entity_ids[:8]:
    ent = entity_map.get(eid, {})
    name = ent.get('text', eid)[:25]
    total_convs = len(convs)

    affinity = {}
    for other_id, other_convs in entity_to_convs.items():
        if other_id == eid:
            continue
        shared = len(convs & other_convs)
        if shared > 50:
            affinity[other_id] = (shared, shared / total_convs)

    top_affinity = sorted(affinity.items(), key=lambda x: x[1][0], reverse=True)[:5]
    if top_affinity:
        print(f'{name:25} (total: {total_convs:,})')
        for other_id, (shared, ratio) in top_affinity:
            other_name = entity_map.get(other_id, {}).get('text', other_id)[:20]
            print(f'  -> {other_name:20} {shared:4,} shared ({ratio*100:.1f}%)')
        print()
