// ============================================
// FOOTER COMPONENT
// ============================================

import { Briefcase, Mail, MapPin, Linkedin, Facebook } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FooterProps {
  className?: string;
}

export function Footer({ className }: FooterProps) {
  return (
    <footer className={cn('bg-secondary text-secondary-foreground', className)}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 bg-primary rounded-lg flex items-center justify-center">
                <Briefcase className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="font-semibold text-lg">ConsultPro</span>
            </div>
            <p className="text-sm text-secondary-foreground/70">
              Plataforma AI-native para identificar oportunidades, preparar propostas e gerir inteligência comercial para consultoria internacional.
            </p>
            <div className="flex gap-4">
              <a
                href="https://www.linkedin.com/company/consultpro-cv"
                target="_blank"
                rel="noopener noreferrer"
                className="text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="h-5 w-5" />
              </a>
              <a
                href="https://www.facebook.com/consultprocv"
                target="_blank"
                rel="noopener noreferrer"
                className="text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                aria-label="Facebook"
              >
                <Facebook className="h-5 w-5" />
              </a>
            </div>
          </div>
          
          {/* Links */}
          <div>
            <h3 className="font-semibold mb-4">Links Rápidos</h3>
            <ul className="space-y-2">
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Sobre Nós
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Funcionalidades
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Preços
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Blog
                </a>
              </li>
            </ul>
          </div>
          
          {/* Support */}
          <div>
            <h3 className="font-semibold mb-4">Suporte</h3>
            <ul className="space-y-2">
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Centro de Ajuda
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Documentação
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  API
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  Contacto
                </a>
              </li>
            </ul>
          </div>
          
          {/* Contact */}
          <div>
            <h3 className="font-semibold mb-4">Contacto</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-2">
                <MapPin className="h-4 w-4 mt-0.5 text-secondary-foreground/70 shrink-0" />
                <span className="text-sm text-secondary-foreground/70">
                  Praia, Cabo Verde
                </span>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-secondary-foreground/70 shrink-0" />
                <a
                  href="mailto:info@consultpro.cv"
                  className="text-sm text-secondary-foreground/70 hover:text-secondary-foreground transition-colors"
                >
                  info@consultpro.cv
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        {/* Bottom */}
        <div className="mt-12 pt-8 border-t border-secondary-foreground/10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-secondary-foreground/50">
              &copy; {new Date().getFullYear()} ConsultPro. Todos os direitos reservados.
            </p>
            <div className="flex gap-6">
              <a
                href="#"
                className="text-sm text-secondary-foreground/50 hover:text-secondary-foreground transition-colors"
              >
                Termos de Uso
              </a>
              <a
                href="#"
                className="text-sm text-secondary-foreground/50 hover:text-secondary-foreground transition-colors"
              >
                Política de Privacidade
              </a>
              <a
                href="#"
                className="text-sm text-secondary-foreground/50 hover:text-secondary-foreground transition-colors"
              >
                Cookies
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
