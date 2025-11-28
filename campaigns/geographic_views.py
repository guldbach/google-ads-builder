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

from .models import GeographicRegion, DanishCity, GeographicRegionUpload


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
