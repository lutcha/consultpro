// ============================================
// FRENCH TRANSLATIONS
// ============================================

export const fr = {
  common: {
    navigation: {
      dashboard: 'Tableau de Bord',
      opportunities: 'Opportunités',
      proposals: 'Propositions',
      teams: 'Équipes',
      settings: 'Paramètres',
      logout: 'Déconnexion',
    },
    actions: {
      save: 'Enregistrer',
      submit: 'Soumettre',
      cancel: 'Annuler',
      edit: 'Modifier',
      delete: 'Supprimer',
      create: 'Créer',
      view: 'Voir',
      download: 'Télécharger',
      upload: 'Téléverser',
      search: 'Rechercher',
      filter: 'Filtrer',
      export: 'Exporter',
      import: 'Importer',
      close: 'Fermer',
      back: 'Retour',
      next: 'Suivant',
      previous: 'Précédent',
      confirm: 'Confirmer',
      apply: 'Appliquer',
      ignore: 'Ignorer',
      resolve: 'Résoudre',
    },
    status: {
      draft: 'Brouillon',
      review: 'En Révision',
      submitted: 'Soumise',
      won: 'Gagnée',
      lost: 'Perdue',
      pending: 'En Attente',
      active: 'Actif',
      inactive: 'Inactif',
    },
    labels: {
      loading: 'Chargement...',
      error: 'Erreur',
      success: 'Succès',
      warning: 'Avertissement',
      info: 'Information',
      noData: 'Aucune donnée',
      searchPlaceholder: 'Rechercher...',
      selectOption: 'Sélectionner une option',
      all: 'Tous',
    },
  },
  dashboard: {
    title: 'Tableau de Bord',
    welcome: 'Bienvenue, {{name}}',
    weeklyReport: 'Rapport Hebdomadaire',
    kpis: {
      activeOpportunities: 'Opportunités Actives',
      proposalsInProgress: 'Propositions en Cours',
      winRate: 'Taux de Réussite',
      upcomingDeadlines: 'Échéances Proches',
    },
    pipeline: {
      title: 'Pipeline de Propositions',
      columns: {
        title: 'Titre',
        client: 'Client',
        deadline: 'Échéance',
        status: 'Statut',
        actions: 'Actions',
      },
    },
    alerts: {
      title: 'Alertes Intelligentes',
    },
    activity: {
      title: 'Activité Récente',
    },
  },
  opportunities: {
    title: 'Opportunités',
    details: {
      title: 'Détails de l\'Opportunité',
      tabs: {
        summary: 'Résumé',
        tor: 'TdR',
        matrix: 'Matrice',
        risks: 'Risques',
      },
      aiSummary: 'Résumé IA',
      requirements: {
        title: 'Exigences Extraites',
        categories: {
          functional: 'Fonctionnelles',
          technical: 'Techniques',
          institutional: 'Institutionnelles',
          financial: 'Financières',
        },
        validateAll: 'Tout Valider',
        export: 'Exporter CSV',
      },
      actions: {
        go: 'Go — Procéder avec la proposition',
        noGo: 'No-Go — Archiver l\'opportunité',
        addNote: 'Ajouter une note interne',
      },
    },
  },
  proposals: {
    title: 'Propositions',
    editor: {
      title: 'Éditeur de Proposition',
      sections: {
        cover: 'Couverture',
        executive_summary: 'Résumé Exécutif',
        methodology: 'Méthodologie',
        team: 'Équipe Technique',
        workplan: 'Plan de Travail',
        budget: 'Budget',
        annexes: 'Annexes',
      },
      aiAssist: {
        title: 'Assistant IA',
        expand: 'Développer le paragraphe',
        summarize: 'Résumer en 100 mots',
        toneFormal: 'Ajuster le ton: plus formel',
        translateEN: 'Traduire en EN',
      },
      sidebar: {
        requirements: 'Exigences du TdR',
        checklist: 'Liste de Conformité',
        suggestions: 'Suggestions IA',
      },
      footer: {
        draft: 'Brouillon',
        save: 'Enregistrer',
        submitQC: 'Soumettre pour CQ',
      },
    },
    qc: {
      title: 'Contrôle Qualité',
      score: 'Score',
      progress: 'Progression',
      categories: {
        compliance: 'Conformité au TdR',
        coherence: 'Cohérence Narrative',
        budget: 'Budget',
        attachments: 'Pièces Jointes',
      },
      actions: {
        rerun: 'Relancer CQ',
        exportReport: 'Exporter le Rapport',
        approve: 'Approuver',
      },
      warnings: {
        minScore: 'Score < 85 bloque la soumission',
      },
    },
  },
  landing: {
    hero: {
      title: 'Automatisez vos propositions de consultation internationale',
      subtitle: 'Plateforme intelligente qui accélère la création, la révision et la soumission de propositions pour l\'ONU, la Banque Mondiale, l\'UE et autres agences.',
      ctaPrimary: 'Entrer sur la Plateforme',
      ctaSecondary: 'Voir la Démo',
    },
    features: {
      title: 'Fonctionnalités',
      items: {
        aiAnalysis: {
          title: 'Analyse IA des TdR',
          description: 'Extraction automatique des exigences, risques et critères d\'évaluation en secondes.',
        },
        teamMatching: {
          title: 'Matching d\'Équipe',
          description: 'Trouvez les consultants idéaux basés sur les compétences, l\'expérience et la disponibilité.',
        },
        qualityCheck: {
          title: 'Contrôle Qualité Automatique',
          description: 'Validation de la conformité au TdR et critères QCBS avant soumission.',
        },
      },
    },
    howItWorks: {
      title: 'Comment Ça Marche',
      steps: {
        upload: {
          number: '1',
          title: 'Téléverser le TdR',
          description: 'Téléversez le document en format PDF ou DOCX',
        },
        analysis: {
          number: '2',
          title: 'Analyse IA',
          description: 'Le système extrait les exigences et suggère une stratégie',
        },
        proposal: {
          number: '3',
          title: 'Proposition Prête',
          description: 'Générez des documents professionnels en minutes',
        },
      },
    },
  },
};
