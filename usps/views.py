from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import models
from .models import USPMainCategory, USPTemplate, USPSet
from campaigns.models import Industry
import json


def usp_manager(request):
    """
    Onepager til at administrere alle USP kategorier og templates
    """
    usp_categories = USPMainCategory.objects.filter(is_active=True).prefetch_related(
        'usptemplate_set__ideal_for_industries'
    ).order_by('sort_order')
    
    industries = Industry.objects.all().order_by('name')
    
    context = {
        'usp_categories': usp_categories,
        'industries': industries,
    }
    
    return render(request, 'usps/usp_manager.html', context)


@csrf_exempt
def create_category_ajax(request):
    """AJAX endpoint til at oprette ny kategori"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            category = USPMainCategory.objects.create(
                name=data.get('name'),
                description=data.get('description'),
                icon=data.get('icon', '⚡'),
                color=data.get('color', '#8B5CF6'),
                sort_order=data.get('sort_order', 1),
                max_selections=data.get('max_selections', 1),
                is_recommended_per_campaign=data.get('is_recommended_per_campaign', True)
            )
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'icon': category.icon,
                    'color': category.color,
                    'sort_order': category.sort_order,
                    'max_selections': category.max_selections,
                    'is_recommended_per_campaign': category.is_recommended_per_campaign
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt  
def create_usp_ajax(request):
    """AJAX endpoint til at oprette ny USP"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Parse comma-separated fields
            use_cases = [case.strip() for case in data.get('use_cases', '').split(',') if case.strip()]
            example_headlines = [hl.strip() for hl in data.get('example_headlines', '').split(',') if hl.strip()]
            placeholders_used = [ph.strip() for ph in data.get('placeholders_used', '').split(',') if ph.strip()]
            short_headlines = [hl.strip() for hl in data.get('short_headlines', '').split(',') if hl.strip()]
            
            category = USPMainCategory.objects.get(id=data.get('main_category'))
            
            usp = USPTemplate.objects.create(
                text=data.get('text'),
                main_category=category,
                priority_rank=data.get('priority_rank', 1),
                explanation=data.get('explanation', ''),
                use_cases=use_cases,
                example_headlines=example_headlines,
                placeholders_used=placeholders_used,
                short_headlines=short_headlines,
                best_for_headline=data.get('best_for_headline', ''),
                best_for_description=data.get('best_for_description', ''),
                effectiveness_score=float(data.get('effectiveness_score', 0.8))
            )
            
            # Add industries
            industry_ids = data.get('ideal_for_industries', [])
            if industry_ids:
                industries = Industry.objects.filter(id__in=industry_ids)
                usp.ideal_for_industries.set(industries)
            
            return JsonResponse({
                'success': True,
                'usp': {
                    'id': usp.id,
                    'text': usp.text,
                    'priority_rank': usp.priority_rank,
                    'explanation': usp.explanation,
                    'use_cases': usp.use_cases,
                    'example_headlines': usp.example_headlines,
                    'placeholders_used': usp.placeholders_used,
                    'effectiveness_score': usp.effectiveness_score
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def duplicate_usp_ajax(request, usp_id):
    """AJAX endpoint til at duplikere USP"""
    if request.method == 'POST':
        try:
            original_usp = get_object_or_404(USPTemplate, id=usp_id)
            
            # Find next available priority rank in the same category
            max_priority = USPTemplate.objects.filter(
                main_category=original_usp.main_category
            ).aggregate(
                max_priority=models.Max('priority_rank')
            )['max_priority'] or 0
            
            # Create duplicate
            new_usp = USPTemplate.objects.create(
                text=f"{original_usp.text} (kopi)",
                main_category=original_usp.main_category,
                category=original_usp.category,
                priority_rank=max_priority + 1,
                explanation=original_usp.explanation,
                use_cases=original_usp.use_cases.copy() if original_usp.use_cases else [],
                example_headlines=original_usp.example_headlines.copy() if original_usp.example_headlines else [],
                short_headlines=original_usp.short_headlines.copy() if original_usp.short_headlines else [],
                best_for_headline=original_usp.best_for_headline,
                best_for_description=original_usp.best_for_description,
                placeholders_used=original_usp.placeholders_used.copy() if original_usp.placeholders_used else [],
                effectiveness_score=original_usp.effectiveness_score,
                urgency_level=original_usp.urgency_level,
                keywords=original_usp.keywords,
                is_active=original_usp.is_active
            )
            
            # Copy industry relationships
            new_usp.ideal_for_industries.set(original_usp.ideal_for_industries.all())
            
            return JsonResponse({
                'success': True,
                'usp_id': new_usp.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def edit_category_ajax(request, category_id):
    """AJAX endpoint til at redigere kategori"""
    if request.method == 'POST':
        try:
            category = get_object_or_404(USPMainCategory, id=category_id)
            data = json.loads(request.body)
            
            category.name = data.get('name', category.name)
            category.description = data.get('description', category.description)
            category.icon = data.get('icon', category.icon)
            category.color = data.get('color', category.color)
            category.sort_order = data.get('sort_order', category.sort_order)
            category.max_selections = data.get('max_selections', category.max_selections)
            category.is_recommended_per_campaign = data.get('is_recommended_per_campaign', category.is_recommended_per_campaign)
            category.save()
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description,
                    'icon': category.icon,
                    'color': category.color,
                    'sort_order': category.sort_order,
                    'max_selections': category.max_selections,
                    'is_recommended_per_campaign': category.is_recommended_per_campaign
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


@csrf_exempt
def edit_usp_ajax(request, usp_id):
    """AJAX endpoint til at redigere USP"""
    if request.method == 'POST':
        try:
            usp = get_object_or_404(USPTemplate, id=usp_id)
            data = json.loads(request.body)
            
            # Parse comma-separated fields
            use_cases = [case.strip() for case in data.get('use_cases', '').split(',') if case.strip()]
            example_headlines = [hl.strip() for hl in data.get('example_headlines', '').split(',') if hl.strip()]
            placeholders_used = [ph.strip() for ph in data.get('placeholders_used', '').split(',') if ph.strip()]
            short_headlines = [hl.strip() for hl in data.get('short_headlines', '').split(',') if hl.strip()]
            
            usp.text = data.get('text', usp.text)
            usp.priority_rank = data.get('priority_rank', usp.priority_rank)
            usp.explanation = data.get('explanation', usp.explanation)
            usp.use_cases = use_cases
            usp.example_headlines = example_headlines
            usp.placeholders_used = placeholders_used
            usp.short_headlines = short_headlines
            usp.best_for_headline = data.get('best_for_headline', usp.best_for_headline)
            usp.best_for_description = data.get('best_for_description', usp.best_for_description)
            usp.effectiveness_score = float(data.get('effectiveness_score', usp.effectiveness_score))
            
            # Update main category if changed
            if data.get('main_category'):
                category = USPMainCategory.objects.get(id=data.get('main_category'))
                usp.main_category = category
            
            usp.save()
            
            # Update industries
            industry_ids = data.get('ideal_for_industries', [])
            if industry_ids:
                industries = Industry.objects.filter(id__in=industry_ids)
                usp.ideal_for_industries.set(industries)
            else:
                usp.ideal_for_industries.clear()
            
            return JsonResponse({
                'success': True,
                'usp': {
                    'id': usp.id,
                    'text': usp.text,
                    'priority_rank': usp.priority_rank,
                    'explanation': usp.explanation,
                    'use_cases': usp.use_cases,
                    'example_headlines': usp.example_headlines,
                    'placeholders_used': usp.placeholders_used,
                    'effectiveness_score': usp.effectiveness_score
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def get_usp_ajax(request, usp_id):
    """AJAX endpoint til at hente USP data til redigering"""
    try:
        usp = get_object_or_404(USPTemplate, id=usp_id)
        
        return JsonResponse({
            'success': True,
            'usp': {
                'id': usp.id,
                'text': usp.text,
                'main_category_id': usp.main_category.id if usp.main_category else None,
                'priority_rank': usp.priority_rank,
                'effectiveness_score': usp.effectiveness_score,
                'explanation': usp.explanation or '',
                'use_cases': ', '.join(usp.use_cases) if usp.use_cases else '',
                'example_headlines': ', '.join(usp.example_headlines) if usp.example_headlines else '',
                'short_headlines': ', '.join(usp.short_headlines) if usp.short_headlines else '',
                'best_for_headline': usp.best_for_headline or '',
                'best_for_description': usp.best_for_description or '',
                'placeholders_used': ', '.join(usp.placeholders_used) if usp.placeholders_used else '',
                'ideal_for_industries': [industry.id for industry in usp.ideal_for_industries.all()]
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def get_category_ajax(request, category_id):
    """AJAX endpoint til at hente kategori data til redigering"""
    try:
        category = get_object_or_404(USPMainCategory, id=category_id)
        
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'icon': category.icon,
                'color': category.color,
                'sort_order': category.sort_order,
                'max_selections': category.max_selections,
                'is_recommended_per_campaign': category.is_recommended_per_campaign
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def delete_usp_ajax(request, usp_id):
    """AJAX endpoint til at slette USP"""
    if request.method == 'POST':
        try:
            usp = get_object_or_404(USPTemplate, id=usp_id)
            usp.delete()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})