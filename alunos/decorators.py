from django.contrib.auth.decorators import user_passes_test

def grupo_required(*nomes_grupos):
    def in_group(user):
        if user.is_superuser:
            return True
        return user.groups.filter(name__in=nomes_grupos).exists()
    return user_passes_test(in_group)