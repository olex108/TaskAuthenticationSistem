from django.apps import AppConfig


class IdentityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "identity"

    def ready(self):
        """
        Registration of custom authorisation for Swagger/OpenAPI.
        """
        try:
            from drf_spectacular.extensions import OpenApiAuthenticationExtension
            from drf_spectacular.plumbing import build_bearer_security_scheme_object

            class CustomJWTAuthExtension(OpenApiAuthenticationExtension):
                target_class = 'identity.authentication.CustomJWTAuthentication'
                name = 'BearerAuth'

                def get_security_definition(self, auto_schema):
                    return build_bearer_security_scheme_object(
                        token_prefix='Bearer',
                        bearer_format='JWT',
                        header_name='Authorization'
                    )

        except ImportError:
            pass
