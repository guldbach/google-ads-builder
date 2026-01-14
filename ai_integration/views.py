"""
Views for AI Integration - Prompt Manager & Loading Widget Manager
"""
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import AIPromptTemplate, LoadingWidget
from .services import build_completion_kwargs


def prompt_manager(request):
    """Main prompt manager page."""
    prompts = AIPromptTemplate.objects.filter(
        prompt_type__in=[
            'generate_descriptions',
            'generate_meta_tags',
            'generate_seo_meta_tags',
            'generate_company_description',
            'perplexity_research',
            'generate_page_content',
            'rewrite_page_content',
            'classify_reviews',
            'extract_usps',
            'detect_services',
        ]
    ).order_by('name')

    return render(request, 'ai_integration/prompt_manager.html', {
        'prompts': prompts
    })


def get_prompt_ajax(request, prompt_id):
    """Get a single prompt's details."""
    try:
        prompt = AIPromptTemplate.objects.get(id=prompt_id)
        return JsonResponse({
            'success': True,
            'prompt': {
                'id': prompt.id,
                'name': prompt.name,
                'prompt_type': prompt.prompt_type,
                'prompt_text': prompt.get_prompt_text(),
                'placeholders': prompt.placeholders,
                'model_settings': prompt.model_settings,
                'is_active': prompt.is_active,
                'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None,
            }
        })
    except AIPromptTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prompt ikke fundet'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def update_prompt_ajax(request, prompt_id):
    """Update a prompt's text and settings."""
    try:
        prompt = AIPromptTemplate.objects.get(id=prompt_id)
        data = json.loads(request.body)

        # Update fields
        if 'prompt_text' in data:
            prompt.prompt_text = data['prompt_text']
            prompt.template = data['prompt_text']  # Keep legacy field in sync

        if 'model_settings' in data:
            prompt.model_settings = data['model_settings']

        if 'placeholders' in data:
            prompt.placeholders = data['placeholders']

        if 'is_active' in data:
            prompt.is_active = data['is_active']

        prompt.save()

        return JsonResponse({
            'success': True,
            'message': 'Prompt opdateret',
            'updated_at': prompt.updated_at.isoformat()
        })

    except AIPromptTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prompt ikke fundet'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_prompt_ajax(request):
    """Test a prompt with sample data and return AI output."""
    try:
        data = json.loads(request.body)
        prompt_id = data.get('prompt_id')
        test_values = data.get('test_values', {})

        prompt = AIPromptTemplate.objects.get(id=prompt_id)
        prompt_text = prompt.get_prompt_text()

        # Replace placeholders with test values
        for placeholder, value in test_values.items():
            prompt_text = prompt_text.replace(placeholder, value)

        # Get model settings
        settings = prompt.model_settings or {}
        model = settings.get('model', 'gpt-4.1')
        temperature = settings.get('temperature', 0.7)
        max_tokens = settings.get('max_tokens', 500)

        from django.conf import settings as django_settings
        from openai import OpenAI

        # Check if model is a Perplexity model (sonar-*)
        is_perplexity = model.startswith('sonar')

        if is_perplexity:
            # Use Perplexity API
            api_key = getattr(django_settings, 'PERPLEXITY_API_KEY', None)
            if not api_key:
                return JsonResponse({
                    'success': False,
                    'error': 'Perplexity API key er ikke konfigureret'
                })

            client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            # Use OpenAI API
            api_key = django_settings.OPENAI_API_KEY
            if not api_key or api_key == 'your_openai_api_key_here':
                return JsonResponse({
                    'success': False,
                    'error': 'OpenAI API key er ikke konfigureret'
                })

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                **build_completion_kwargs(model, [{"role": "user", "content": prompt_text}], temperature, max_tokens)
            )

        output = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens if response.usage else 0

        return JsonResponse({
            'success': True,
            'output': output,
            'tokens_used': tokens_used,
            'model_used': model,
            'prompt_preview': prompt_text[:500] + '...' if len(prompt_text) > 500 else prompt_text
        })

    except AIPromptTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prompt ikke fundet'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =====================================================
# Loading Widget Manager Views
# =====================================================

def loading_widget_manager(request):
    """Main loading widget manager page."""
    # Order: active first, then by priority (desc), then by name
    widgets = LoadingWidget.objects.all().order_by('-is_active', '-priority', 'name')
    operation_types = LoadingWidget.OPERATION_TYPES

    return render(request, 'ai_integration/loading_widget_manager.html', {
        'widgets': widgets,
        'operation_types': operation_types
    })


def get_widget_ajax(request, widget_id):
    """Get a single widget's details."""
    try:
        widget = LoadingWidget.objects.get(id=widget_id)
        return JsonResponse({
            'success': True,
            'widget': {
                'id': widget.id,
                'name': widget.name,
                'operation_type': widget.operation_type,
                'svg_content': widget.svg_content,
                'text_config': widget.get_text_config(),
                'css_class': widget.css_class,
                'is_active': widget.is_active,
                'priority': widget.priority,
                'updated_at': widget.updated_at.isoformat() if widget.updated_at else None,
            }
        })
    except LoadingWidget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Widget ikke fundet'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def create_widget_ajax(request):
    """Create a new loading widget."""
    try:
        data = json.loads(request.body)

        widget = LoadingWidget.objects.create(
            name=data.get('name', 'Ny Widget'),
            operation_type=data.get('operation_type', 'random'),
            svg_content=data.get('svg_content', ''),
            text_config=data.get('text_config', {}),
            css_class=data.get('css_class', ''),
            is_active=data.get('is_active', True),
            priority=data.get('priority', 0)
        )

        return JsonResponse({
            'success': True,
            'message': 'Widget oprettet',
            'widget_id': widget.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_widget_ajax(request, widget_id):
    """Update a loading widget."""
    try:
        widget = LoadingWidget.objects.get(id=widget_id)
        data = json.loads(request.body)

        # Update fields if provided
        if 'name' in data:
            widget.name = data['name']
        if 'operation_type' in data:
            widget.operation_type = data['operation_type']
        if 'svg_content' in data:
            widget.svg_content = data['svg_content']
        if 'text_config' in data:
            widget.text_config = data['text_config']
        if 'css_class' in data:
            widget.css_class = data['css_class']
        if 'is_active' in data:
            widget.is_active = data['is_active']
        if 'priority' in data:
            widget.priority = data['priority']

        widget.save()

        return JsonResponse({
            'success': True,
            'message': 'Widget opdateret',
            'updated_at': widget.updated_at.isoformat()
        })

    except LoadingWidget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Widget ikke fundet'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST", "DELETE"])
def delete_widget_ajax(request, widget_id):
    """Delete a loading widget."""
    try:
        widget = LoadingWidget.objects.get(id=widget_id)
        widget.delete()

        return JsonResponse({
            'success': True,
            'message': 'Widget slettet'
        })

    except LoadingWidget.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Widget ikke fundet'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def get_widgets_for_operation(request):
    """
    Get all active widgets grouped by operation type.
    Used by frontend to fetch widgets on page load.
    """
    widgets = LoadingWidget.objects.filter(is_active=True)

    # Group widgets by operation type
    grouped = {}
    for widget in widgets:
        op_type = widget.operation_type
        if op_type not in grouped:
            grouped[op_type] = []

        grouped[op_type].append({
            'id': widget.id,
            'name': widget.name,
            'svg_content': widget.svg_content,
            'text_config': widget.get_text_config(),
            'css_class': widget.css_class,
            'priority': widget.priority
        })

    # Sort each group by priority (descending)
    for op_type in grouped:
        grouped[op_type].sort(key=lambda x: -x['priority'])

    return JsonResponse({
        'success': True,
        'widgets': grouped
    })
