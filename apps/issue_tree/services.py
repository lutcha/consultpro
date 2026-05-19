from django.db import transaction
from django.db.models import Max

from apps.proposals.models import Proposal, ProposalSection

from .models import IssueTreeNode, IssueTreeSnapshot


SECTION_TO_ISSUE = {
    'executive_summary': 'strategic_case',
    'methodology': 'technical_solution',
    'team': 'delivery_capacity',
    'workplan': 'delivery_capacity',
    'budget': 'commercial_readiness',
    'annexes': 'compliance_readiness',
}

DEFAULT_ISSUES = [
    {
        'key': 'strategic_case',
        'title': 'Why should the client select this proposal?',
        'hypothesis': 'The proposal wins if it clearly connects client priorities, sector insight, and a credible value proposition.',
        'data_needed': ['Client priorities', 'evaluation criteria', 'win themes'],
    },
    {
        'key': 'technical_solution',
        'title': 'How will the work be delivered credibly?',
        'hypothesis': 'The methodology should translate the ToR into a practical delivery approach with evidence and sequencing.',
        'data_needed': ['ToR requirements', 'methodology assumptions', 'delivery risks'],
    },
    {
        'key': 'delivery_capacity',
        'title': 'Can the proposed team execute with confidence?',
        'hypothesis': 'The team narrative should prove relevant experience, availability, and role clarity.',
        'data_needed': ['Key experts', 'CV evidence', 'workplan responsibilities'],
    },
    {
        'key': 'commercial_readiness',
        'title': 'Is the offer commercially and administratively ready?',
        'hypothesis': 'The proposal should be compliant, priced coherently, and ready for submission without late-stage blockers.',
        'data_needed': ['Budget assumptions', 'submission checklist', 'mandatory documents'],
    },
]


def _section_issue_key(section_type):
    return SECTION_TO_ISSUE.get(section_type, 'technical_solution')


def _snapshot_nodes(proposal):
    nodes = IssueTreeNode.objects.filter(proposal=proposal).order_by('parent_id', 'order', 'id')
    return {
        'proposal_id': proposal.id,
        'nodes': [
            {
                'id': node.id,
                'parent_id': node.parent_id,
                'source_key': node.source_key,
                'node_type': node.node_type,
                'title': node.title,
                'hypothesis': node.hypothesis,
                'data_needed': node.data_needed,
                'assigned_to': node.assigned_to_id,
                'proposal_section': node.proposal_section_id,
                'status': node.status,
                'order': node.order,
                'source_trace': node.source_trace,
            }
            for node in nodes
        ],
    }


@transaction.atomic
def generate_issue_tree(proposal_id, generated_by=None):
    proposal = Proposal.objects.select_related('opportunity').get(id=proposal_id)
    ai_metadata = {
        'provider': 'deterministic',
        'model': 'issue_tree_v1',
        'strategy': 'mece_proposal_preparation',
    }
    root, _ = IssueTreeNode.objects.update_or_create(
        proposal=proposal,
        source_key='root',
        defaults={
            'parent': None,
            'node_type': 'root',
            'title': f'Win-ready proposal: {proposal.title}',
            'hypothesis': 'A complete proposal must answer the client question, prove delivery credibility, and remove submission risk.',
            'data_needed': ['Evaluation criteria', 'ToR requirements', 'proposal sections', 'team evidence'],
            'order': 0,
            'source_trace': [{'source': 'proposal', 'id': proposal.id}],
            'ai_metadata': ai_metadata,
            'created_by': generated_by,
        },
    )

    issue_nodes = {}
    for order, issue in enumerate(DEFAULT_ISSUES, start=1):
        node, _ = IssueTreeNode.objects.update_or_create(
            proposal=proposal,
            source_key=f"issue:{issue['key']}",
            defaults={
                'parent': root,
                'node_type': 'issue',
                'title': issue['title'],
                'hypothesis': issue['hypothesis'],
                'data_needed': issue['data_needed'],
                'order': order,
                'source_trace': [{'source': 'issue_tree_template', 'key': issue['key']}],
                'ai_metadata': ai_metadata,
                'created_by': generated_by,
            },
        )
        issue_nodes[issue['key']] = node

    for section in proposal.sections.all().order_by('order', 'id'):
        issue_key = _section_issue_key(section.section_type)
        parent = issue_nodes.get(issue_key, root)
        IssueTreeNode.objects.update_or_create(
            proposal=proposal,
            source_key=f'section:{section.id}',
            defaults={
                'parent': parent,
                'node_type': 'hypothesis',
                'title': f'Use "{section.title}" to support {parent.title}',
                'hypothesis': section.content[:500] if section.content else 'Section needs a sharper hypothesis and evidence.',
                'data_needed': ['Section evidence', 'client proof points', 'missing assumptions'],
                'proposal_section': section,
                'order': section.order,
                'source_trace': [{'source': 'proposal_section', 'id': section.id, 'section_type': section.section_type}],
                'ai_metadata': ai_metadata,
                'created_by': generated_by,
            },
        )

    for order, requirement in enumerate(proposal.opportunity.requirements.all().order_by('id'), start=1):
        parent = issue_nodes.get('compliance_readiness', root)
        IssueTreeNode.objects.update_or_create(
            proposal=proposal,
            source_key=f'requirement:{requirement.id}',
            defaults={
                'parent': parent,
                'node_type': 'evidence',
                'title': requirement.description[:255],
                'hypothesis': 'This requirement must be visibly addressed or waived before submission.',
                'data_needed': [requirement.category, requirement.priority],
                'order': order,
                'source_trace': [{'source': 'opportunity_requirement', 'id': requirement.id}],
                'ai_metadata': ai_metadata,
                'created_by': generated_by,
            },
        )

    return root


@transaction.atomic
def create_issue_tree_snapshot(proposal_id, label='', created_by=None):
    proposal = Proposal.objects.get(id=proposal_id)
    next_version = (
        IssueTreeSnapshot.objects.filter(proposal=proposal).aggregate(max_version=Max('version'))['max_version'] or 0
    ) + 1
    return IssueTreeSnapshot.objects.create(
        proposal=proposal,
        version=next_version,
        label=label,
        snapshot=_snapshot_nodes(proposal),
        created_by=created_by,
    )


def validate_node_scope(proposal, parent=None, proposal_section=None):
    if parent and parent.proposal_id != proposal.id:
        raise ValueError('Parent node must belong to the same proposal.')
    if proposal_section and proposal_section.proposal_id != proposal.id:
        raise ValueError('Proposal section must belong to the same proposal.')
