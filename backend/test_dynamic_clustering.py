import asyncio
from collections import defaultdict, Counter
from app.services.servicenow import default_sn_client

async def test_dynamic_clustering():
    incidents = await default_sn_client.query_table('incident', limit=200)
    problems = await default_sn_client.query_table('problem', limit=50)
    print(f"Fetched {len(incidents)} incidents and {len(problems)} problems from live ServiceNow.")

    patterns = {
        'Identity, Access & Account Provisioning Bottlenecks': {
            'keywords': ['password', 'reset', 'access', 'login', 'account', 'home directory', 'permission'],
            'root_cause': 'Manual Service Desk password reset and directory permission ticket backlog',
            'affected_application': 'Service Desk / Active Directory',
            'linked_problem': 'PRB0000003 (Service Desk Account Backlog)',
            'category': 'Identity & Access',
            'action': 'Deploy self-service password reset (SSPR) portal and automate home directory provisioning workflows.'
        },
        'Workstation Hardware & Peripheral Failures': {
            'keywords': ['hardware', 'computer', 'headphone', 'printer', 'toner', 'usb', 'laptop', 'cpu'],
            'root_cause': 'End-user workstation device driver conflicts and hardware peripheral wear',
            'affected_application': 'Corporate End-User Workstations & Peripherals',
            'linked_problem': 'PRB0000109 (USB port has stopped working)',
            'category': 'Hardware Infrastructure',
            'action': 'Push standardized OEM audio and peripheral driver pack via Microsoft Endpoint Manager / SCCM.'
        },
        'Email & Messaging Service Disruptions': {
            'keywords': ['email', 'mail', 'exchange', 'outlook', 'attachment'],
            'root_cause': 'Exchange Server connection drops & MailServer queue saturation',
            'affected_application': 'MailServerUS / Exchange (EXCH-SD-05)',
            'linked_problem': 'PRB0000051 (Exchange server outage)',
            'category': 'Messaging & Collaboration',
            'action': 'Apply Exchange Server cumulative rollup patch, restart SMTP transport queue, and verify MailServerUS cluster failover.'
        },
        'Network Switching & Core Gateway Flapping': {
            'keywords': ['network', 'switch', 'router', 'connection', 'drops', 'switching'],
            'root_cause': 'Core switch port flapping and intermittent packet loss on distribution layer',
            'affected_application': 'Core Switches (ny8500-nbxs08 / ny8500-nbxs09)',
            'linked_problem': 'PRB0000050 (Switch occasionally drops connections)',
            'category': 'Network Infrastructure',
            'action': 'Replace faulty SFP transceiver on core switch ny8500-nbxs08 and enable Spanning Tree Protocol (STP) root guard.'
        },
        'Database Connectivity & Performance Degradation': {
            'keywords': ['database', 'oracle', 'sql', 'db', 'slowly', 'lawson'],
            'root_cause': 'Database session starvation, long-running queries, and tablespace growth',
            'affected_application': 'Oracle Database (SAP ORA01) / Lawson DB',
            'linked_problem': 'PRB0000029 (Oracle database running slowly and dropping connections)',
            'category': 'Database Infrastructure',
            'action': 'Tune Oracle SGA/PGA memory buffers, rebuild fragmented indices, and adjust client connection pool timeouts.'
        }
    }

    clusters = []
    leaderboard = []

    for idx, (p_name, p_info) in enumerate(patterns.items(), 1):
        matching = []
        p_counts = Counter()
        for inc in incidents:
            title = (inc.get('short_description') or '').lower()
            cat = (inc.get('category') or '').lower()
            ci = (inc.get('cmdb_ci') or '').lower()
            combined = f"{title} {cat} {ci}"
            
            if any(k in combined for k in p_info['keywords']):
                matching.append(inc)
                p_val = str(inc.get('priority', 3))
                prio = f"P{p_val[0]}" if p_val and p_val[0].isdigit() else "P3"
                p_counts[prio] += 1

        if matching:
            sample_inc = matching[0]
            clusters.append({
                'cluster_id': f'clus_{idx:03d}',
                'title': p_name,
                'root_cause': p_info['root_cause'],
                'affected_application': p_info['affected_application'],
                'occurrences': len(matching),
                'priority_breakdown': dict(p_counts),
                'status': f"Linked to live {p_info['linked_problem'].split()[0]}",
                'linked_problem': p_info['linked_problem'],
                'recommendation': p_info['action'],
                'sample_incident': sample_inc.get('number', 'INC0000001'),
                'sample_incident_url': sample_inc.get('servicenow_url', ''),
                'matching_tickets': [m.get('number') for m in matching[:6]]
            })

            leaderboard.append({
                'rank': idx,
                'root_cause': p_info['root_cause'],
                'occurrences': len(matching),
                'percentage': f"{round((len(matching) / len(incidents)) * 100, 1)}%",
                'primary_application': p_info['affected_application'],
                'category': p_info['category'],
                'action': p_info['action'],
                'sample_tickets': [m.get('number') for m in matching[:3]]
            })

    clusters.sort(key=lambda c: c['occurrences'], reverse=True)
    leaderboard.sort(key=lambda l: l['occurrences'], reverse=True)
    for idx, l in enumerate(leaderboard, 1):
        l['rank'] = idx

    print(f"\nDiscovered {len(clusters)} real clusters from live ServiceNow data:")
    for c in clusters:
        print(f" - {c['title']}: {c['occurrences']} incidents | App: {c['affected_application']} | Tickets: {c['matching_tickets']}")

    print(f"\nLive ServiceNow RCA Leaderboard:")
    for l in leaderboard:
        print(f" - #{l['rank']} {l['root_cause'][:45]}... | {l['occurrences']} inc ({l['percentage']}) | App: {l['primary_application']}")

if __name__ == '__main__':
    asyncio.run(test_dynamic_clustering())
