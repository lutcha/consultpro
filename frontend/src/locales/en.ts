// ============================================
// ENGLISH TRANSLATIONS
// ============================================

export const en = {
  common: {
    navigation: {
      dashboard: 'Dashboard',
      opportunities: 'Opportunities',
      proposals: 'Proposals',
      teams: 'Teams',
      settings: 'Settings',
      logout: 'Logout',
    },
    actions: {
      save: 'Save',
      submit: 'Submit',
      cancel: 'Cancel',
      edit: 'Edit',
      delete: 'Delete',
      create: 'Create',
      view: 'View',
      download: 'Download',
      upload: 'Upload',
      search: 'Search',
      filter: 'Filter',
      export: 'Export',
      import: 'Import',
      close: 'Close',
      back: 'Back',
      next: 'Next',
      previous: 'Previous',
      confirm: 'Confirm',
      apply: 'Apply',
      ignore: 'Ignore',
      resolve: 'Resolve',
    },
    status: {
      draft: 'Draft',
      review: 'In Review',
      submitted: 'Submitted',
      won: 'Won',
      lost: 'Lost',
      pending: 'Pending',
      active: 'Active',
      inactive: 'Inactive',
    },
    labels: {
      loading: 'Loading...',
      error: 'Error',
      success: 'Success',
      warning: 'Warning',
      info: 'Information',
      noData: 'No data',
      searchPlaceholder: 'Search...',
      selectOption: 'Select option',
      all: 'All',
    },
  },
  dashboard: {
    title: 'Dashboard',
    welcome: 'Welcome, {{name}}',
    weeklyReport: 'Weekly Report',
    kpis: {
      activeOpportunities: 'Active Opportunities',
      proposalsInProgress: 'Proposals in Progress',
      winRate: 'Win Rate',
      upcomingDeadlines: 'Upcoming Deadlines',
    },
    pipeline: {
      title: 'Proposal Pipeline',
      columns: {
        title: 'Title',
        client: 'Client',
        deadline: 'Deadline',
        status: 'Status',
        actions: 'Actions',
      },
    },
    alerts: {
      title: 'Smart Alerts',
    },
    activity: {
      title: 'Recent Activity',
    },
  },
  opportunities: {
    title: 'Opportunities',
    details: {
      title: 'Opportunity Details',
      tabs: {
        summary: 'Summary',
        tor: 'ToR',
        matrix: 'Matrix',
        risks: 'Risks',
      },
      aiSummary: 'AI Summary',
      requirements: {
        title: 'Extracted Requirements',
        categories: {
          functional: 'Functional',
          technical: 'Technical',
          institutional: 'Institutional',
          financial: 'Financial',
        },
        validateAll: 'Validate All',
        export: 'Export CSV',
      },
      actions: {
        go: 'Go — Proceed with proposal',
        noGo: 'No-Go — Archive opportunity',
        addNote: 'Add internal note',
      },
    },
  },
  proposals: {
    title: 'Proposals',
    editor: {
      title: 'Proposal Editor',
      sections: {
        cover: 'Cover',
        executive_summary: 'Executive Summary',
        methodology: 'Methodology',
        team: 'Technical Team',
        workplan: 'Work Plan',
        budget: 'Budget',
        annexes: 'Annexes',
      },
      aiAssist: {
        title: 'AI Assistant',
        expand: 'Expand paragraph',
        summarize: 'Summarize to 100 words',
        toneFormal: 'Adjust tone: more formal',
        translateEN: 'Translate to EN',
      },
      sidebar: {
        requirements: 'ToR Requirements',
        checklist: 'Compliance Checklist',
        suggestions: 'AI Suggestions',
      },
      footer: {
        draft: 'Draft',
        save: 'Save',
        submitQC: 'Submit for QC',
      },
    },
    qc: {
      title: 'Quality Check',
      score: 'Score',
      progress: 'Progress',
      categories: {
        compliance: 'ToR Compliance',
        coherence: 'Narrative Coherence',
        budget: 'Budget',
        attachments: 'Attachments',
      },
      actions: {
        rerun: 'Re-run QC',
        exportReport: 'Export Report',
        approve: 'Approve',
      },
      warnings: {
        minScore: 'Score < 85 blocks submission',
      },
    },
  },
  landing: {
    hero: {
      title: 'Automate your international consulting proposals',
      subtitle: 'Intelligent platform that accelerates the creation, review, and submission of proposals for UN, World Bank, EU, and other agencies.',
      ctaPrimary: 'Enter Platform',
      ctaSecondary: 'View Demo',
    },
    features: {
      title: 'Features',
      items: {
        aiAnalysis: {
          title: 'AI ToR Analysis',
          description: 'Automatic extraction of requirements, risks, and evaluation criteria in seconds.',
        },
        teamMatching: {
          title: 'Team Matching',
          description: 'Find ideal consultants based on skills, experience, and availability.',
        },
        qualityCheck: {
          title: 'Automatic Quality Check',
          description: 'Validation of ToR compliance and QCBS criteria before submission.',
        },
      },
    },
    howItWorks: {
      title: 'How It Works',
      steps: {
        upload: {
          number: '1',
          title: 'Upload ToR',
          description: 'Upload the document in PDF or DOCX format',
        },
        analysis: {
          number: '2',
          title: 'AI Analysis',
          description: 'System extracts requirements and suggests strategy',
        },
        proposal: {
          number: '3',
          title: 'Proposal Ready',
          description: 'Generate professional documents in minutes',
        },
      },
    },
  },
};
