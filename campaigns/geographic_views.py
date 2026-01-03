# Geographic Regions Manager Views
# These views handle the management of Danish cities organized by geographic regions

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
import json
import pandas as pd
import io
from decimal import Decimal

from .models import GeographicRegion, DanishCity, GeographicRegionUpload, PostalCode, NegativeKeywordList, NegativeKeyword


def geographic_regions_manager(request):
    """Modern geographic regions manager with enhanced UI"""
    if request.user.is_authenticated:
        geographic_regions = GeographicRegion.objects.filter(
            created_by=request.user
        ).prefetch_related('cities').order_by('-created_at')
    else:
        # For demo purposes, show all regions when not authenticated
        geographic_regions = GeographicRegion.objects.all().prefetch_related('cities').order_by('-created_at')
    
    context = {
        'geographic_regions': geographic_regions,
    }
    
    return render(request, 'campaigns/geographic_regions_manager.html', context)


@csrf_exempt
def create_geographic_region_ajax(request):
    """Create a new geographic region via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Parse form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', 'custom').strip()
        icon = request.POST.get('icon', '🗺️').strip()
        color = request.POST.get('color', '#3B82F6').strip()
        is_active = request.POST.get('is_active') == 'true'
        
        # Validate required fields
        if not name:
            return JsonResponse({'success': False, 'error': 'Navn er påkrævet'})
        
        
        # For demo purposes, create a dummy user if none exists
        from django.contrib.auth.models import User
        if not request.user.is_authenticated:
            demo_user, created = User.objects.get_or_create(
                username='demo_user',
                defaults={'email': 'demo@example.com', 'first_name': 'Demo', 'last_name': 'User'}
            )
        else:
            demo_user = request.user

        # Create the geographic region
        region = GeographicRegion.objects.create(
            name=name,
            description=description,
            category=category,
            icon=icon,
            color=color,
            is_active=is_active,
            created_by=demo_user
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Region "{name}" blev oprettet!',
            'region_id': region.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt
def add_danish_city_ajax(request):
    """Add a new Danish city to a geographic region via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        region_id = request.POST.get('region_id', '').strip()
        city_name = request.POST.get('city_name', '').strip()
        city_synonym = request.POST.get('city_synonym', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        
        # Validate required fields
        if not region_id or not city_name:
            return JsonResponse({'success': False, 'error': 'Region og bynavn er påkrævet'})
        
        # Get the geographic region
        try:
            region = GeographicRegion.objects.get(id=region_id)
        except GeographicRegion.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Region ikke fundet'})
        
        # Check if city already exists in this region (case-insensitive)
        if postal_code:
            # If postal code provided, check both name and postal code
            if DanishCity.objects.filter(region=region, city_name__iexact=city_name, postal_code=postal_code).exists():
                return JsonResponse({'success': False, 'error': f'By "{city_name}" med postnummer {postal_code} eksisterer allerede i denne region'})
        else:
            # If no postal code, just check city name (case-insensitive)
            if DanishCity.objects.filter(region=region, city_name__iexact=city_name).exists():
                return JsonResponse({'success': False, 'error': f'By "{city_name}" eksisterer allerede i denne region'})
        
        # Convert coordinates to Decimal if provided
        lat_decimal = None
        lng_decimal = None
        if latitude:
            try:
                lat_decimal = Decimal(latitude)
            except:
                return JsonResponse({'success': False, 'error': 'Ugyldig breddegrad format'})
        
        if longitude:
            try:
                lng_decimal = Decimal(longitude)
            except:
                return JsonResponse({'success': False, 'error': 'Ugyldig længdegrad format'})
        
        # Create the city
        city = DanishCity.objects.create(
            region=region,
            city_name=city_name,
            city_synonym=city_synonym if city_synonym else '',
            postal_code=postal_code if postal_code else '',
            latitude=lat_decimal,
            longitude=lng_decimal
        )
        
        # Update the region's cities count
        region.cities_count = region.cities.count()
        region.save()
        
        return JsonResponse({
            'success': True,
            'message': f'By "{city_name}" blev tilføjet!',
            'city': {
                'id': city.id,
                'city_name': city.city_name,
                'city_synonym': city.city_synonym,
                'postal_code': city.postal_code,
                'coordinates': f"{city.latitude}, {city.longitude}" if city.latitude and city.longitude else ""
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt 
def delete_danish_city_ajax(request, city_id):
    """Delete a Danish city via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        city = get_object_or_404(DanishCity, id=city_id)
        region = city.region
        city_name = city.city_name
        
        # Delete the city
        city.delete()
        
        # Update the region's cities count
        region.cities_count = region.cities.count()
        region.save()
        
        return JsonResponse({
            'success': True,
            'message': f'By "{city_name}" blev slettet!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt
def suggest_postal_code_ajax(request):
    """
    Suggest a postal code for a city name based on DAWA data.
    Uses average of existing postal codes in the region to pick the closest match
    when multiple postal codes match the same city name.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        city_name = request.POST.get('city_name', '').strip()
        region_id = request.POST.get('region_id', '').strip()

        if not city_name:
            return JsonResponse({'success': False, 'error': 'Bynavn er påkrævet'})

        # Check for MULTI postal code cities (København, Frederiksberg, Vesterbro)
        # These cities have many consolidated postal codes and should be marked as MULTI
        MULTI_POSTAL_CITIES = ['københavn', 'frederiksberg', 'vesterbro']
        if city_name.lower() in MULTI_POSTAL_CITIES:
            return JsonResponse({
                'success': True,
                'found': True,
                'postal_code': 'MULTI',
                'postal_name': city_name,
                'suggestions': [],
                'method': 'multi_postal_city',
                'message': f'{city_name} har mange konsoliderede postnumre'
            })

        # Find all postal codes that match this city name
        matching_postals = []

        # Search in dawa_name (exact match, case-insensitive)
        for postal in PostalCode.objects.filter(dawa_name__iexact=city_name):
            matching_postals.append({
                'code': postal.code,
                'name': postal.get_display_name(),
                'source': 'dawa_name'
            })

        # Search in display_name (exact match, case-insensitive)
        for postal in PostalCode.objects.filter(display_name__iexact=city_name):
            if postal.code not in [p['code'] for p in matching_postals]:
                matching_postals.append({
                    'code': postal.code,
                    'name': postal.get_display_name(),
                    'source': 'display_name'
                })

        # Search in additional_names (contains, case-insensitive)
        for postal in PostalCode.objects.filter(additional_names__icontains=city_name):
            # Verify exact match in the comma-separated list
            additional = postal.get_additional_names_list()
            if any(name.lower() == city_name.lower() for name in additional):
                if postal.code not in [p['code'] for p in matching_postals]:
                    matching_postals.append({
                        'code': postal.code,
                        'name': postal.get_display_name(),
                        'source': 'additional_names'
                    })

        if not matching_postals:
            return JsonResponse({
                'success': True,
                'found': False,
                'message': f'Ingen postnumre fundet for "{city_name}"',
                'suggestions': []
            })

        # If only one match, return it directly
        if len(matching_postals) == 1:
            return JsonResponse({
                'success': True,
                'found': True,
                'postal_code': matching_postals[0]['code'],
                'postal_name': matching_postals[0]['name'],
                'suggestions': matching_postals,
                'method': 'single_match'
            })

        # Multiple matches - calculate average of existing region postal codes
        suggested_code = None
        method = 'first_match'

        if region_id:
            try:
                region = GeographicRegion.objects.get(id=region_id)
                existing_codes = list(region.cities.exclude(postal_code='').values_list('postal_code', flat=True))

                if existing_codes:
                    # Calculate average of existing postal codes
                    numeric_codes = [int(c) for c in existing_codes if c.isdigit() and len(c) == 4]
                    if numeric_codes:
                        avg_code = sum(numeric_codes) / len(numeric_codes)

                        # Find the matching postal code closest to the average
                        closest = min(
                            matching_postals,
                            key=lambda p: abs(int(p['code']) - avg_code)
                        )
                        suggested_code = closest['code']
                        method = f'closest_to_average_{int(avg_code)}'
            except GeographicRegion.DoesNotExist:
                pass

        # If no suggestion from average, use the first match
        if not suggested_code:
            suggested_code = matching_postals[0]['code']

        suggested_postal = next((p for p in matching_postals if p['code'] == suggested_code), matching_postals[0])

        return JsonResponse({
            'success': True,
            'found': True,
            'postal_code': suggested_postal['code'],
            'postal_name': suggested_postal['name'],
            'suggestions': matching_postals,
            'method': method,
            'multiple_matches': True
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt
def update_danish_city_ajax(request, city_id):
    """Update a Danish city via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        city = get_object_or_404(DanishCity, id=city_id)
        
        city_name = request.POST.get('city_name', '').strip()
        city_synonym = request.POST.get('city_synonym', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        latitude = request.POST.get('latitude', '').strip()
        longitude = request.POST.get('longitude', '').strip()
        
        # Validate required fields
        if not city_name:
            return JsonResponse({'success': False, 'error': 'Bynavn er påkrævet'})
        
        # Check for duplicate city name in same region (excluding current city)
        if DanishCity.objects.filter(
            region=city.region, 
            city_name=city_name
        ).exclude(id=city_id).exists():
            return JsonResponse({'success': False, 'error': f'By "{city_name}" eksisterer allerede i denne region'})
        
        # Convert coordinates to Decimal if provided
        lat_decimal = None
        lng_decimal = None
        if latitude:
            try:
                lat_decimal = Decimal(latitude)
            except:
                return JsonResponse({'success': False, 'error': 'Ugyldig breddegrad format'})
        
        if longitude:
            try:
                lng_decimal = Decimal(longitude)
            except:
                return JsonResponse({'success': False, 'error': 'Ugyldig længdegrad format'})
        
        # Update the city
        city.city_name = city_name
        city.city_synonym = city_synonym if city_synonym else ''
        city.postal_code = postal_code
        city.latitude = lat_decimal
        city.longitude = lng_decimal
        city.save()
        
        return JsonResponse({
            'success': True,
            'message': f'By "{city_name}" blev opdateret!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt
def delete_geographic_region_ajax(request, region_id):
    """Delete a geographic region via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        region = get_object_or_404(GeographicRegion, id=region_id)
        region_name = region.name
        cities_count = region.cities.count()
        
        # Delete the region (this will cascade to delete all cities)
        region.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Region "{region_name}" og {cities_count} byer blev slettet!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt
def edit_geographic_region_ajax(request, region_id):
    """Edit geographic region details via AJAX"""
    if request.method == 'GET':
        # Return region details for editing
        try:
            region = get_object_or_404(GeographicRegion, id=region_id)
            return JsonResponse({
                'success': True,
                'region': {
                    'id': region.id,
                    'name': region.name,
                    'description': region.description or '',
                    'category': region.category,
                    'icon': region.icon,
                    'color': region.color,
                    'is_active': region.is_active
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})
    
    elif request.method == 'POST':
        # Update region details
        try:
            region = get_object_or_404(GeographicRegion, id=region_id)
            
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', 'custom').strip()
            icon = request.POST.get('icon', '🗺️').strip()
            color = request.POST.get('color', '#3B82F6').strip()
            is_active = request.POST.get('is_active') == 'true'
            
            # Validate required fields
            if not name:
                return JsonResponse({'success': False, 'error': 'Navn er påkrævet'})
            
            
            # Update the region
            region.name = name
            region.description = description
            region.category = category
            region.icon = icon
            region.color = color
            region.is_active = is_active
            region.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Region "{name}" blev opdateret!'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


def download_danish_cities_template(request):
    """Download Excel template for importing Danish cities"""
    import pandas as pd
    from django.http import HttpResponse
    
    # Create simplified sample data - only city names in column A
    sample_data = {
        'Bynavn': [
            'København',
            'Aarhus', 
            'Odense',
            'Aalborg',
            'Esbjerg',
            'Randers',
            'Kolding',
            'Horsens',
            'Vejle',
            'Roskilde'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Danske Byer')
        
        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Danske Byer']
        
        # Add some formatting
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="danske_byer_template.xlsx"'
    
    return response


@csrf_exempt
def import_danish_cities_excel(request):
    """Import Danish cities from Excel file"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    if 'excel_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Ingen fil uploadet'})
    
    # Get region_id from POST data
    region_id = request.POST.get('region_id')
    if not region_id:
        return JsonResponse({'success': False, 'error': 'Region ID mangler'})
    
    excel_file = request.FILES['excel_file']
    
    try:
        result = process_danish_cities_excel(excel_file, request.user if request.user.is_authenticated else None, region_id)
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl ved import: {str(e)}'})


def process_danish_cities_excel(excel_file, user, region_id=None):
    # For demo purposes, create a dummy user if none exists
    from django.contrib.auth.models import User
    if not user or not user.is_authenticated:
        demo_user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={'email': 'demo@example.com', 'first_name': 'Demo', 'last_name': 'User'}
        )
        user = demo_user
    """Process uploaded Excel file and create geographic regions and cities"""
    try:
        # Read Excel file
        df = pd.read_excel(excel_file, engine='openpyxl')
        
        # Expected columns - simplified to only require city names
        required_columns = ['Bynavn']
        
        # Check if required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {
                'success': False,
                'error': f'Manglende kolonner: {", ".join(missing_columns)}'
            }
        
        # Process data
        created_cities = 0
        processed_rows = 0
        skipped_rows = 0
        errors = []
        
        with transaction.atomic():
            for index, row in df.iterrows():
                processed_rows += 1
                
                try:
                    # Extract only city name from simplified template
                    city_name = str(row['Bynavn']).strip() if pd.notna(row['Bynavn']) else ''
                    
                    # Validate required fields
                    if not city_name:
                        skipped_rows += 1
                        continue
                    
                    # Get the target region
                    if region_id:
                        # Import to specific region (new simplified approach)
                        try:
                            region = GeographicRegion.objects.get(id=region_id)
                        except GeographicRegion.DoesNotExist:
                            return {
                                'success': False,
                                'error': f'Region med ID {region_id} findes ikke'
                            }
                    else:
                        # Fallback: create a default region if no region_id provided
                        region, created = GeographicRegion.objects.get_or_create(
                            name='Importeret Excel Data',
                            created_by=user,
                            defaults={
                                'description': f'Automatisk oprettet fra Excel import',
                                'category': 'custom',
                                'icon': '🗺️',
                                'color': '#3B82F6',
                                'is_active': True
                            }
                        )
                    
                    # Check if city already exists (simplified - only check city name in region)
                    if not DanishCity.objects.filter(
                        region=region,
                        city_name=city_name
                    ).exists():
                        # Create city with simplified data (only city name)
                        DanishCity.objects.create(
                            region=region,
                            city_name=city_name,
                            city_synonym='',  # Empty as per simplified template
                            postal_code='',   # Empty as per simplified template
                            latitude=None,    # No coordinates in simplified template
                            longitude=None,   # No coordinates in simplified template
                            source_file_line=index + 2  # +2 because pandas starts at 0 and Excel header is row 1
                        )
                        created_cities += 1
                    else:
                        skipped_rows += 1
                
                except Exception as e:
                    errors.append(f'Række {index + 2}: {str(e)}')
                    skipped_rows += 1
                    continue
        
        # Update cities count for the target region
        if region_id:
            try:
                region = GeographicRegion.objects.get(id=region_id)
                region.cities_count = region.cities.count()
                region.save()
            except GeographicRegion.DoesNotExist:
                pass
        
        # Return results
        return {
            'success': True,
            'summary': {
                'created_cities': created_cities,
                'processed_rows': processed_rows,
                'skipped_rows': skipped_rows,
                'errors': errors[:10]  # Limit to first 10 errors
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Fejl ved læsning af Excel fil: {str(e)}'
        }


@csrf_exempt
def analyze_excel_import_cities(request, region_id):
    """AJAX endpoint to analyze Excel import for cities with duplicate detection"""
    if request.method == 'POST':
        try:
            import openpyxl
            
            # Get the region
            try:
                region = GeographicRegion.objects.get(id=region_id)
            except GeographicRegion.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Region ikke fundet'})
            
            # Get uploaded file
            excel_file = request.FILES.get('excel_file')
            if not excel_file:
                return JsonResponse({'success': False, 'error': 'Ingen fil uploadet'})
            
            # Parse file (support both Excel and CSV)
            import_cities = []
            file_name = excel_file.name.lower()
            
            try:
                if file_name.endswith('.csv'):
                    # Handle CSV files
                    import csv
                    import io
                    
                    # Read CSV content
                    file_content = excel_file.read().decode('utf-8')
                    csv_reader = csv.reader(io.StringIO(file_content))
                    
                    # Skip header row and read cities
                    next(csv_reader, None)  # Skip header
                    for row_num, row in enumerate(csv_reader, 2):
                        if row and len(row) > 0 and row[0]:  # If there's text in first column
                            city_name = str(row[0]).strip()
                            if city_name:
                                import_cities.append({
                                    'city_name': city_name,
                                    'row_number': row_num
                                })
                else:
                    # Handle Excel files
                    workbook = openpyxl.load_workbook(excel_file)
                    worksheet = workbook.active
                    
                    # Read cities from Excel
                    for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), 2):
                        if row[0]:  # If there's text in first column
                            city_name = str(row[0]).strip()
                            if city_name:
                                import_cities.append({
                                    'city_name': city_name,
                                    'row_number': row_num
                                })
                
                if not import_cities:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Ingen bynavne fundet i Excel filen'
                    })
                
                # Check for duplicates against existing cities in region
                existing_cities = set(
                    DanishCity.objects.filter(region=region)
                    .values_list('city_name', flat=True)
                )
                
                # Categorize cities
                new_cities = []
                duplicate_cities = []
                
                for city in import_cities:
                    if city['city_name'] in existing_cities:
                        duplicate_cities.append(city)
                    else:
                        new_cities.append(city)
                
                # Return analysis results
                return JsonResponse({
                    'success': True,
                    'region_name': region.name,
                    'total_read': len(import_cities),
                    'unique_cities': len(set([city['city_name'] for city in import_cities])),
                    'new_cities': len(new_cities),
                    'duplicates': len(duplicate_cities),
                    'cities_preview': [city['city_name'] for city in new_cities],
                    'duplicate_cities': [city['city_name'] for city in duplicate_cities],
                    'cities_to_add': new_cities
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Fejl ved læsning af Excel fil: {str(e)}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Uventet fejl: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def execute_excel_import_cities(request, region_id):
    """AJAX endpoint to execute the actual city import after analysis"""
    if request.method == 'POST':
        try:
            import openpyxl
            
            # Get the region
            try:
                region = GeographicRegion.objects.get(id=region_id)
            except GeographicRegion.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Region ikke fundet'})
            
            # Get cities to add from JSON body
            try:
                request_data = json.loads(request.body)
                cities_to_add = request_data.get('cities', [])
            except json.JSONDecodeError:
                # Fallback to POST data for backward compatibility
                cities_to_add = json.loads(request.POST.get('cities_to_add', '[]'))
            
            if not cities_to_add:
                return JsonResponse({'success': False, 'error': 'Ingen byer angivet til import'})
            
            # Skip Excel parsing - we already have the cities from analyze step
            
            # Create cities that were selected for addition
            created_cities = []
            skipped_cities = []
            
            try:
                with transaction.atomic():
                    for city_name in cities_to_add:
                        # Double-check for duplicates
                        if not DanishCity.objects.filter(region=region, city_name=city_name).exists():
                            city = DanishCity.objects.create(
                                region=region,
                                city_name=city_name,
                                city_synonym='',
                                postal_code='',
                                latitude=None,
                                longitude=None
                            )
                            created_cities.append({
                                'id': city.id,
                                'city_name': city.city_name
                            })
                        else:
                            skipped_cities.append(city_name)
                    
                    # Update region cities count
                    region.cities_count = region.cities.count()
                    region.save()
                
                # If we get here, everything worked
                return JsonResponse({
                    'success': True,
                    'message': f'{len(created_cities)} byer tilføjet til {region.name}!',
                    'cities_added': len(created_cities),
                    'results': {
                        'created_cities': created_cities,
                        'skipped_cities': skipped_cities,
                        'total_created': len(created_cities),
                        'total_skipped': len(skipped_cities)
                    }
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Fejl ved import: {str(e)}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Uventet fejl: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



def download_danish_cities_template(request):
    """Download Excel template for importing Danish cities"""
    import pandas as pd
    from django.http import HttpResponse
    import io

    # Create simplified sample data - only city names in column A
    sample_data = {
        'Bynavn': [
            'København',
            'Aarhus',
            'Odense',
            'Aalborg',
            'Esbjerg',
            'Randers',
            'Kolding',
            'Horsens',
            'Vejle',
            'Roskilde'
        ]
    }

    df = pd.DataFrame(sample_data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Danske Byer')

        # Get workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Danske Byer']

        # Add some formatting
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 30)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="danske_byer_template.xlsx"'

    return response


# ============================================================================
# NEGATIVE CITY LIST GENERATION
# ============================================================================

def get_all_city_names():
    """
    Hent alle danske bynavne fra PostalCode tabellen.
    Returnerer et set af alle unikke bynavne i lowercase.
    """
    all_names = set()
    for postal in PostalCode.objects.all():
        # Tilføj dawa_name (det officielle navn)
        if postal.dawa_name:
            all_names.add(postal.dawa_name.lower())

        # Tilføj display_name hvis det findes
        if postal.display_name:
            all_names.add(postal.display_name.lower())

        # Tilføj alle additional_names
        for name in postal.get_additional_names_list():
            if name:
                all_names.add(name.lower())

    return all_names


@csrf_exempt
def generate_negative_city_list(request):
    """
    Generer eller opdater den singleton negativ søgeordsliste for alle danske byer der IKKE er valgt.

    Bruger altid den samme liste "Ekskluderede Byer" - opretter den hvis den ikke findes,
    ellers opdateres den eksisterende.

    POST data:
    - selected_cities: Liste af valgte bynavne (fra geo_map_targeting.postal_names)

    Returns:
    - success: True/False
    - list_id: ID på listen
    - list_name: Navn på listen
    - keywords_count: Antal negative keywords
    - selected_count: Antal valgte byer
    - updated: True hvis eksisterende liste blev opdateret
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        selected_cities_raw = data.get('selected_cities', [])

        # Konverter valgte byer til lowercase for sammenligning
        selected_cities = set(c.lower() for c in selected_cities_raw if c)

        if not selected_cities:
            return JsonResponse({
                'success': False,
                'error': 'Ingen byer valgt. Vælg først nogle byer/regioner.'
            })

        # Hent alle bynavne
        all_cities = get_all_city_names()

        # Simpel logik: alle byer minus de valgte = negative keywords
        excluded = all_cities - selected_cities

        # Håndter bruger (demo_user hvis ikke authenticated)
        from django.contrib.auth.models import User
        if not request.user.is_authenticated:
            demo_user, _ = User.objects.get_or_create(
                username='demo_user',
                defaults={'email': 'demo@example.com', 'first_name': 'Demo', 'last_name': 'User'}
            )
        else:
            demo_user = request.user

        # SINGLETON PATTERN: Find eller opret den ene "Ekskluderede Byer" liste
        negative_list = NegativeKeywordList.objects.filter(
            name='Ekskluderede Byer',
            category='location'
        ).first()

        if negative_list:
            # Opdater eksisterende liste - slet alle keywords først
            NegativeKeyword.objects.filter(keyword_list=negative_list).delete()
            negative_list.description = f'Auto-genereret: {len(excluded)} byer ekskluderet, {len(selected_cities)} byer valgt'
            negative_list.save(update_fields=['description'])
            updated = True
        else:
            # Opret ny liste (første gang)
            negative_list = NegativeKeywordList.objects.create(
                name='Ekskluderede Byer',
                category='location',
                icon='🚫',
                color='#EF4444',
                description=f'Auto-genereret: {len(excluded)} byer ekskluderet, {len(selected_cities)} byer valgt',
                created_by=demo_user
            )
            updated = False

        # Tilføj keywords (bulk_create for performance) - wrapped i transaction for at sikre commit
        keywords = [
            NegativeKeyword(
                keyword_list=negative_list,
                keyword_text=city,
                match_type='broad'
            )
            for city in sorted(excluded)
        ]

        with transaction.atomic():
            NegativeKeyword.objects.bulk_create(keywords)

        # Hent faktisk count fra database EFTER commit for at sikre korrekthed
        actual_count = negative_list.negative_keywords.count()

        # Opdater keywords_count på listen med database count
        negative_list.keywords_count = actual_count
        negative_list.save(update_fields=['keywords_count'])

        action = 'opdateret' if updated else 'oprettet'
        return JsonResponse({
            'success': True,
            'list_id': negative_list.id,
            'list_name': negative_list.name,
            'keywords_count': actual_count,  # Brug database count
            'selected_count': len(selected_cities),
            'updated': updated,
            'message': f'Negativ liste "{negative_list.name}" {action} med {actual_count} byer'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Ugyldig JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Fejl: {str(e)}'})


@csrf_exempt
def get_negative_city_count(request):
    """
    Hent antal byer der ville blive ekskluderet baseret på valgte byer.
    Bruges til live opdatering af visning uden at ændre databasen.

    POST data:
    - selected_cities: Liste af valgte bynavne

    Returns:
    - count: Antal byer der ville blive ekskluderet
    - selected: Antal valgte byer
    - total: Totalt antal danske bynavne
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        selected_cities_raw = data.get('selected_cities', [])

        # Konverter valgte byer til lowercase for sammenligning
        selected_cities = set(c.lower() for c in selected_cities_raw if c)

        # Hent alle bynavne
        all_cities = get_all_city_names()

        # Beregn antal ekskluderede
        excluded_count = len(all_cities - selected_cities)

        return JsonResponse({
            'count': excluded_count,
            'selected': len(selected_cities),
            'total': len(all_cities)
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Ugyldig JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Fejl: {str(e)}'}, status=500)
