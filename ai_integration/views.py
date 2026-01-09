"""
Views for AI Integration - Prompt Manager
"""
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import AIPromptTemplate


def prompt_manager(request):
    """Main prompt manager page."""
    prompts = AIPromptTemplate.objects.filter(
        prompt_type__in=[
            'generate_descriptions',
            'generate_meta_tags',
            'generate_seo_meta_tags',
            'generate_company_description',
            'perplexity_research'
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

        # Call OpenAI API
        from django.conf import settings as django_settings
        from openai import OpenAI

        api_key = django_settings.OPENAI_API_KEY
        if not api_key or api_key == 'your_openai_api_key_here':
            return JsonResponse({
                'success': False,
                'error': 'OpenAI API key er ikke konfigureret'
            })

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt_text}],
            temperature=temperature,
            max_tokens=max_tokens
        )

        output = response.choices[0].message.content.strip()
        tokens_used = response.usage.total_tokens if response.usage else 0

        return JsonResponse({
            'success': True,
            'output': output,
            'tokens_used': tokens_used,
            'prompt_preview': prompt_text[:500] + '...' if len(prompt_text) > 500 else prompt_text
        })

    except AIPromptTemplate.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Prompt ikke fundet'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
