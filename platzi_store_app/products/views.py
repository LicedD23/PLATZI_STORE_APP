# products/views.py
from django.shortcuts import render
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .forms import ProductForm  # Importar el formulario
import requests
import json

# URL base de la API de Platzi Store
PLATZI_API_BASE_URL = "https://api.escuelajs.co/api/v1"

def products_menu_views(request):
    """Vista para consultar todos los productos de la API de Platzi Store"""
    
    # Parámetros de consulta
    page = request.GET.get('page', 1)
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    try:
        # Construir URL de la API
        api_url = f"{PLATZI_API_BASE_URL}/products"
        params = {}
        
        # Agregar parámetros si existen
        if search:
            # La API de Platzi permite filtrar por título
            params['title'] = search
        
        if category_id:
            params['categoryId'] = category_id
        
        # Realizar petición a la API
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        # Obtener productos
        products_data = response.json()
        
        # Obtener categorías para el filtro
        categories_response = requests.get(f"{PLATZI_API_BASE_URL}/categories", timeout=10)
        categories_data = categories_response.json() if categories_response.status_code == 200 else []
        
        # Paginación manual
        paginator = Paginator(products_data, 12)  # 12 productos por página
        page_obj = paginator.get_page(page)
        
        # Estadísticas básicas
        stats = {
            'total_products': len(products_data),
            'total_categories': len(categories_data),
            'current_page': page,
            'total_pages': paginator.num_pages
        }
        
        context = {
            'page_obj': page_obj,
            'products': page_obj.object_list,
            'categories': categories_data,
            'stats': stats,
            'search_query': search,
            'selected_category': category_id,
            'title': 'Platzi Store - Consultar Productos',
            'api_status': 'success'
        }
        
    except requests.exceptions.RequestException as e:
        # Error de conexión con la API
        messages.error(
            request, 
            f'Error al conectar con la API de Platzi Store: {str(e)}'
        )
        context = {
            'products': [],
            'categories': [],
            'stats': {'total_products': 0, 'total_categories': 0},
            'title': 'Platzi Store - Error de Conexión',
            'api_status': 'error',
            'error_message': str(e)
        }
    
    except json.JSONDecodeError:
        # Error al decodificar la respuesta JSON
        messages.error(
            request, 
            'Error al procesar la respuesta de la API'
        )
        context = {
            'products': [],
            'categories': [],
            'stats': {'total_products': 0, 'total_categories': 0},
            'title': 'Platzi Store - Error de Datos',
            'api_status': 'error'
        }
    
    return render(request, 'products/product_list.html', context)

def add_product(request):
    """Vista para agregar nuevos productos a la API de Platzi Store"""
    
    # Obtener categorías para el formulario
    categories = []
    try:
        categories_response = requests.get(f"{PLATZI_API_BASE_URL}/categories", timeout=10)
        if categories_response.status_code == 200:
            categories = categories_response.json()
    except requests.exceptions.RequestException:
        messages.warning(
            request, 
            'No se pudieron cargar las categorías. Intenta recargar la página.'
        )
    
    if request.method == 'POST':
        # Usar el formulario de Django
        form = ProductForm(request.POST)
        
        if form.is_valid():
            try:
                # Obtener datos del formulario usando el método get_product_data()
                product_data = form.get_product_data()
                
                # Enviar datos a la API
                response = requests.post(
                    f"{PLATZI_API_BASE_URL}/products/",
                    json=product_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 201:
                    # Producto creado exitosamente
                    created_product = response.json()
                    messages.success(
                        request, 
                        f'¡Producto "{created_product.get("title", "")}" agregado exitosamente!'
                    )
                    
                    # Crear formulario vacío para el siguiente producto
                    form = ProductForm()
                else:
                    # Error del servidor
                    try:
                        error_data = response.json()
                        error_message = error_data.get('message', f'Error del servidor: {response.status_code}')
                    except:
                        error_message = f'Error del servidor: {response.status_code}'
                    
                    messages.error(request, f'No se pudo crear el producto: {error_message}')
            
            except requests.exceptions.RequestException as e:
                messages.error(
                    request, 
                    f'Error de conexión con la API: {str(e)}'
                )
            except Exception as e:
                messages.error(
                    request, 
                    f'Error inesperado: {str(e)}'
                )
        else:
            # El formulario tiene errores - se mostrarán automáticamente en el template
            messages.error(request, 'Por favor corrige los errores en el formulario')
    
    else:
        # GET request - mostrar formulario vacío
        form = ProductForm()
    
    context = {
        'form': form,
        'categories': categories,
        'title': 'Agregar Producto - Platzi Store',
    }
    
    return render(request, 'products/add_product.html', context)

def get_product_detail(request, product_id):
    """Vista auxiliar para obtener detalles de un producto específico (opcional)"""
    
    try:
        response = requests.get(
            f"{PLATZI_API_BASE_URL}/products/{product_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            product = response.json()
            context = {
                'product': product,
                'title': f'{product.get("title", "Producto")} - Platzi Store'
            }
        else:
            messages.error(request, 'Producto no encontrado')
            context = {
                'product': None,
                'title': 'Producto no encontrado - Platzi Store'
            }
    
    except requests.exceptions.RequestException as e:
        messages.error(request, f'Error al obtener producto: {str(e)}')
        context = {
            'product': None,
            'title': 'Error - Platzi Store'
        }
    
    return render(request, 'products/product_detail.html', context)
