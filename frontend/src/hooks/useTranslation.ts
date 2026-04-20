// ============================================
// TRANSLATION HOOK
// ============================================

import { useState, useCallback } from 'react';
import { pt } from '@/locales/pt';
import { en } from '@/locales/en';
import { fr } from '@/locales/fr';

type Locale = 'pt' | 'en' | 'fr';

const translations = {
  pt,
  en,
  fr,
};

export function useTranslation(_namespace: string = 'common') {
  const [locale, setLocale] = useState<Locale>('pt');
  
  const t = useCallback(
    (key: string) => {
      const keys = key.split('.');
      let value: unknown = translations[locale];
      
      for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
          value = (value as Record<string, unknown>)[k];
        } else {
          return key; // Return key if translation not found
        }
      }
      
      return typeof value === 'string' ? value : key;
    },
    [locale]
  );
  
  const changeLocale = useCallback((newLocale: Locale) => {
    setLocale(newLocale);
    document.documentElement.lang = newLocale;
  }, []);
  
  return {
    t,
    locale,
    changeLocale,
  };
}
