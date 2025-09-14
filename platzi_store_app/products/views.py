# products/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required  # Añadir esta importación
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
            'api_status': 'success',
            # ✅ SOLUCIÓN: Explícitamente pasar el usuario al contexto
            'user': request.user,  # Esta es la línea clave que faltaba
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
            'error_message': str(e),
            # ✅ SOLUCIÓN: También en el caso de error
            'user': request.user,
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
            'api_status': 'error',
        }
    
    return render(request, 'products/product_list.html', context)


@login_required  # ✅ MEJORA: Requerir autenticación para agregar productos
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
    
    return render(request, 'products/product_list.html', context)

@login_required  # ✅ MEJORA: Requerir autenticación para actualizar productos
def update_product(request, product_id):
    """Vista para mostrar el formulario de actualización de un producto específico.""" 
    if request.method == 'GET': 
        try: 
            # Obtener el producto
            response = requests.get(f"{PLATZI_API_BASE_URL}/products/{product_id}", timeout=10) 
            if response.status_code == 200: 
                product = response.json() 
                category_id = product.get('categoryId', None)  # Obtener ID de categoría
                
                # Obtener categorías
                categories_response = requests.get(f"{PLATZI_API_BASE_URL}/categories", timeout=10)
                if categories_response.status_code == 200:
                    categories = categories_response.json()  # Suponiendo que es una lista de categorías
                else:
                    categories = []  # Manejar el caso de error

                # Inicializar el formulario
                form = ProductForm(initial={ 
                    'title': product['title'],
                    'price': product['price'], 
                    'description': product['description'], 
                    'category': category_id,  # Usar category_id
                    'image_url': product['images'][0] if product['images'] else ''
                }) 
                
                context = {
                    'form': form, 
                    'categories': categories,  # Pasar las categorías al contexto
                    'title': f'Actualizar Producto - {product["title"]}', 
                }
                return render(request, 'products/update_product.html', context)  # Cambiar a update_product.html
            else: 
                messages.error(request, 'Producto no encontrado') 
                return redirect('products:products_menu_views') 
        except requests.exceptions.RequestException as e: 
            messages.error(request, f'Error al obtener el producto: {str(e)}') 
            return redirect('products:products_menu_views') 
    elif request.method == 'POST':
        form = request.POST 
        try:
            updated_data = { 
                "title": form.get('title'), 
                "price": form.get('price'), 
                "description": form.get('description'), 
                "categoryId": form.get('category', None), 
                "images": [form.get('image_url')] if form.get('image_url') else [] 
            }
            
            response = requests.put( 
                f"{PLATZI_API_BASE_URL}/products/{product_id}", 
                json=updated_data, 
                headers={'Content-Type': 'application/json'}, 
                timeout=10 
            ) 
            if response.status_code == 200:
                messages.success(request, 'Producto actualizado exitosamente!') 
            else: 
                messages.error(request, 'Error al actualizar el producto.') 
        except requests.exceptions.RequestException as e: 
            messages.error(request, f'Error de conexión con la API: {str(e)}') 
        return redirect('products:products_menu_views')


@login_required  # ✅ MEJORA: Requerir autenticación para eliminar productos
def delete_product(request, product_id):
    # Obtener información del producto antes de eliminar para mostrarla
    product_data = None
    try:
        get_response = requests.get(f"{PLATZI_API_BASE_URL}/products/{product_id}")
        if get_response.status_code == 200:
            product_data = get_response.json()
    except requests.exceptions.RequestException:
        pass

    if request.method == 'POST':
        try:
            # Verificar que el producto exista
            if not product_data:
                get_response = requests.get(f"{PLATZI_API_BASE_URL}/products/{product_id}")
                if get_response.status_code == 404:
                    messages.error(request, "El producto no existe.")
                    return redirect('products:products_menu_views')

            # Intentar eliminar el producto
            response = requests.delete(
                f"{PLATZI_API_BASE_URL}/products/{product_id}",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                messages.success(request, f'Producto "{product_data.get("title", "")}" eliminado exitosamente!')
            else:
                error_message = "Error al eliminar el producto."
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', error_message)
                except ValueError:
                    pass
                messages.error(request, f'No se pudo eliminar el producto: {error_message}')
                
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Error de conexión con la API: {str(e)}')

        return redirect('products:products_menu_views')

    # Pasar datos del producto al template para mostrar información
    context = {
        'product': product_data,
        'product_id': product_id
    }
    return render(request, 'products/delete_product.html', context)