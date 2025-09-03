# products/forms.py
from django import forms
import requests

class ProductForm(forms.Form):
    """Formulario para crear productos en la API de Platzi Store"""
    
    title = forms.CharField(
        max_length=200,
        label='Título del Producto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: iPhone 14 Pro Max',
            'required': True
        })
    )
    
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label='Precio',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01',
            'required': True
        })
    )
    
    description = forms.CharField(
        label='Descripción',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe las características principales del producto...',
            'rows': 4,
            'required': True
        })
    )
    
    categoryId = forms.ChoiceField(
        label='Categoría',
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    # Campo corregido para URLs de imágenes
    image_url_1 = forms.URLField(
        label='URL de Imagen 1',
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com/imagen1.jpg'
        })
    )
    
    image_url_2 = forms.URLField(
        label='URL de Imagen 2',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com/imagen2.jpg (opcional)'
        })
    )
    
    image_url_3 = forms.URLField(
        label='URL de Imagen 3',
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com/imagen3.jpg (opcional)'
        })
    )
    
    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y carga las categorías desde la API"""
        super().__init__(*args, **kwargs)
        self.load_categories()
    
    def load_categories(self):
        """Carga las categorías desde la API de Platzi Store"""
        try:
            response = requests.get(
                "https://api.escuelajs.co/api/v1/categories",
                timeout=10
            )
            if response.status_code == 200:
                categories = response.json()
                choices = [('', 'Selecciona una categoría')]
                choices.extend([(cat['id'], cat['name']) for cat in categories])
                self.fields['categoryId'].choices = choices
            else:
                self.fields['categoryId'].choices = [('', 'Error al cargar categorías')]
        except requests.exceptions.RequestException:
            self.fields['categoryId'].choices = [('', 'Error de conexión - Recarga la página')]
    
    def clean_title(self):
        """Valida que el título no esté vacío"""
        title = self.cleaned_data['title'].strip()
        if not title:
            raise forms.ValidationError('El título del producto es requerido')
        return title
    
    def clean_price(self):
        """Valida que el precio sea mayor a 0"""
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0')
        return price
    
    def clean_description(self):
        """Valida que la descripción no esté vacía"""
        description = self.cleaned_data['description'].strip()
        if not description:
            raise forms.ValidationError('La descripción del producto es requerida')
        return description
    
    def clean_categoryId(self):
        """Valida que se haya seleccionado una categoría válida"""
        category_id = self.cleaned_data['categoryId']
        if not category_id:
            raise forms.ValidationError('Debes seleccionar una categoría válida')
        try:
            return int(category_id)
        except (ValueError, TypeError):
            raise forms.ValidationError('Categoría inválida')
    
    def clean(self):
        """Validación adicional del formulario completo"""
        cleaned_data = super().clean()
        return cleaned_data
    
    def get_product_data(self):
        """Convierte los datos del formulario al formato esperado por la API"""
        if not self.is_valid():
            return None
        
        # Recolectar todas las URLs de imágenes que no estén vacías
        image_urls = []
        for i in range(1, 4):
            url = self.cleaned_data.get(f'image_url_{i}')
            if url:
                image_urls.append(url)
        
        return {
            "title": self.cleaned_data['title'],
            "price": float(self.cleaned_data['price']),
            "description": self.cleaned_data['description'],
            "categoryId": self.cleaned_data['categoryId'],
            "images": image_urls
        }


class ProductSearchForm(forms.Form):
    """Formulario para filtrar y buscar productos"""
    
    search = forms.CharField(
        max_length=200,
        required=False,
        label='Buscar productos',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título...'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        label='Filtrar por categoría',
        choices=[],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y carga las categorías"""
        super().__init__(*args, **kwargs)
        self.load_categories()
    
    def load_categories(self):
        """Carga las categorías para el filtro"""
        try:
            response = requests.get(
                "https://api.escuelajs.co/api/v1/categories",
                timeout=10
            )
            if response.status_code == 200:
                categories = response.json()
                choices = [('', 'Todas las categorías')]
                choices.extend([(cat['id'], cat['name']) for cat in categories])
                self.fields['category'].choices = choices
        except requests.exceptions.RequestException:
            self.fields['category'].choices = [('', 'Error al cargar categorías')]