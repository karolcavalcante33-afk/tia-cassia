from pathlib import Path

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# Chave de segurança (Mantenha em sigilo em produção)
SECRET_KEY = 'django-insecure-trocar-essa-chave'

# Modo de depuração ativado para desenvolvimento
DEBUG = True

ALLOWED_HOSTS = ["tia-cassia.onrender.com"]

# Aplicativos instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'alunos', # Seu app do projeto tia-cassia
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'tia_cassia.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tia_cassia.wsgi.application'

# Banco de dados SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configurações de Localização (Brasil)
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_L10N = True  
USE_TZ = False
USE_THOUSAND_SEPARATOR = True
DECIMAL_SEPARATOR = ','
NUMBER_GROUPING = 3

# Arquivos Estáticos (CSS, JS, Imagens)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========================================================
# CONFIGURAÇÕES DE AUTENTICAÇÃO E REDIRECIONAMENTO
# ========================================================

# Página para onde o usuário é mandado se tentar acessar algo sem logar
LOGIN_URL = "/login/"

# MUDANÇA ESSENCIAL: Agora todos caem na lista de alunos ao logar.
# Isso evita que a funcionária seja barrada logo no início, 
# já que ela não tem acesso ao dashboard financeiro (/) que criamos.
LOGIN_REDIRECT_URL = "lista_alunos" 

# Página para onde o usuário vai ao sair do sistema
LOGOUT_REDIRECT_URL = "/login/"