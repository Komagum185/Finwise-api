# MSE Category System Documentation

## Overview

The Finwise system now supports different MSE (Micro and Small Enterprise) categories with their own individual tables and specialized fields. This allows for better data organization, category-specific analytics, and tailored business management features.

## MSE Categories

### 1. Input MSE (Input Market MSE)
**Focus:** Sourcing raw materials and inputs for other businesses

**Key Characteristics:**
- Sources raw materials, supplies, and inputs
- Maintains supplier networks
- Tracks input costs and quality standards
- Manages storage and logistics

**Specialized Fields:**
- `input_categories`: Categories of inputs sourced
- `supplier_network_size`: Number of suppliers in network
- `average_order_value`: Average value of input orders
- `lead_time_days`: Average lead time for inputs
- `quality_standards`: Quality standards maintained
- `storage_capacity`: Storage capacity description
- `primary_inputs`: List of primary inputs sourced
- `seasonal_inputs`: Seasonal inputs and their periods
- `input_costs_tracking`: Track input costs separately

**API Endpoints:**
- `GET /api/mses/input-mses/` - List all Input MSEs
- `POST /api/mses/input-mses/` - Create new Input MSE
- `PUT /api/mses/input-mses/{id}/` - Update Input MSE
- `DELETE /api/mses/input-mses/{id}/` - Delete Input MSE
- `GET /api/mses/input-mses/statistics/` - Get Input MSE statistics

### 2. Output MSE (Output Market MSE)
**Focus:** Selling products and services to customers

**Key Characteristics:**
- Sells products and services
- Maintains customer networks
- Implements marketing strategies
- Manages sales channels and distribution

**Specialized Fields:**
- `output_categories`: Categories of outputs sold
- `customer_network_size`: Number of customers in network
- `average_sale_value`: Average value of sales
- `sales_channels`: Sales channels used
- `marketing_strategy`: Marketing strategy description
- `primary_products`: List of primary products/services
- `seasonal_products`: Seasonal products and their periods
- `pricing_strategy`: Pricing strategy used
- `delivery_methods`: Delivery methods offered

**API Endpoints:**
- `GET /api/mses/output-mses/` - List all Output MSEs
- `POST /api/mses/output-mses/` - Create new Output MSE
- `PUT /api/mses/output-mses/{id}/` - Update Output MSE
- `DELETE /api/mses/output-mses/{id}/` - Delete Output MSE
- `GET /api/mses/output-mses/statistics/` - Get Output MSE statistics

### 3. Production MSE (Production/Manufacturing MSE)
**Focus:** Manufacturing and processing products

**Key Characteristics:**
- Manufactures and processes products
- Manages production capacity and efficiency
- Maintains equipment and quality control
- Tracks production metrics and safety protocols

**Specialized Fields:**
- `production_capacity`: Production capacity description
- `production_process`: Production process description
- `equipment_list`: List of production equipment
- `quality_control`: Quality control procedures
- `raw_materials_required`: Raw materials required for production
- `production_cycle_time`: Production cycle time
- `waste_management`: Waste management procedures
- `safety_protocols`: Safety protocols
- `daily_production_target`: Daily production target
- `efficiency_metrics`: Production efficiency metrics
- `maintenance_schedule`: Equipment maintenance schedule

**API Endpoints:**
- `GET /api/mses/production-mses/` - List all Production MSEs
- `POST /api/mses/production-mses/` - Create new Production MSE
- `PUT /api/mses/production-mses/{id}/` - Update Production MSE
- `DELETE /api/mses/production-mses/{id}/` - Delete Production MSE
- `GET /api/mses/production-mses/statistics/` - Get Production MSE statistics

### 4. Hybrid MSE
**Focus:** Operates in multiple categories (Input, Output, and/or Production)

**Key Characteristics:**
- Combines multiple business functions
- Can source inputs, produce goods, and sell products
- Requires more complex management and analytics
- Tracks performance across multiple categories

## Database Schema

### Base MSE Model
```python
class MSE(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    mse_type = models.CharField(choices=[('micro', 'Micro'), ('small', 'Small')])
    status = models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')])
    # ... other common fields
```

### Category-Specific Models
```python
class InputMSE(models.Model):
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE)
    # Input-specific fields

class OutputMSE(models.Model):
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE)
    # Output-specific fields

class ProductionMSE(models.Model):
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE)
    # Production-specific fields
```

### Category Classification
```python
class MSECategory(models.Model):
    mse = models.OneToOneField(MSE, on_delete=models.CASCADE)
    primary_category = models.CharField(choices=[
        ('input', 'Input MSE'),
        ('output', 'Output MSE'),
        ('production', 'Production MSE'),
        ('hybrid', 'Hybrid MSE'),
    ])
    secondary_categories = models.JSONField(default=list)
    # ... performance metrics
```

## API Usage Examples

### Creating an Input MSE
```javascript
// Frontend API call
const inputMseData = {
  mse: 1, // MSE ID
  input_categories: ['raw_materials', 'supplies'],
  supplier_network_size: 15,
  average_order_value: 5000.00,
  lead_time_days: 7,
  quality_standards: 'ISO 9001 compliant',
  storage_capacity: '1000 sq ft warehouse',
  primary_inputs: ['steel', 'plastic', 'electronics'],
  seasonal_inputs: [{'item': 'agricultural_products', 'season': 'harvest'}],
  input_costs_tracking: true
};

const response = await api.inputMses.create(inputMseData);
```

### Creating an Output MSE
```javascript
const outputMseData = {
  mse: 2, // MSE ID
  output_categories: ['finished_goods', 'services'],
  customer_network_size: 50,
  average_sale_value: 2500.00,
  sales_channels: ['retail', 'online', 'wholesale'],
  marketing_strategy: 'Digital marketing with social media presence',
  primary_products: ['furniture', 'home_decor'],
  seasonal_products: [{'item': 'holiday_decorations', 'season': 'christmas'}],
  pricing_strategy: 'competitive_pricing',
  delivery_methods: ['local_delivery', 'shipping']
};

const response = await api.outputMses.create(outputMseData);
```

### Creating a Production MSE
```javascript
const productionMseData = {
  mse: 3, // MSE ID
  production_capacity: '500 units per day',
  production_process: 'Assembly line with quality checkpoints',
  equipment_list: ['conveyor_belts', 'packaging_machines', 'quality_testers'],
  quality_control: 'Multi-stage quality inspection process',
  raw_materials_required: ['steel', 'plastic', 'electronics'],
  production_cycle_time: '2 hours per unit',
  waste_management: 'Recycling program for scrap materials',
  safety_protocols: 'OSHA compliant safety procedures',
  daily_production_target: 500,
  efficiency_metrics: {'oee': 85, 'downtime': 5},
  maintenance_schedule: 'Weekly preventive maintenance'
};

const response = await api.productionMses.create(productionMseData);
```

### Getting Category Statistics
```javascript
// Get Input MSE statistics
const inputStats = await api.inputMses.getStatistics();

// Get Output MSE statistics
const outputStats = await api.outputMses.getStatistics();

// Get Production MSE statistics
const productionStats = await api.productionMses.getStatistics();

// Get overall category summary
const categorySummary = await api.mseCategories.getSummary();
```

## Business Logic Features

### 1. Category-Specific Analytics
- **Input MSEs**: Track supplier performance, input costs, lead times
- **Output MSEs**: Monitor sales performance, customer satisfaction, market trends
- **Production MSEs**: Measure production efficiency, quality metrics, capacity utilization

### 2. Cross-Category Relationships
- Input MSEs can supply to Production MSEs
- Production MSEs can supply to Output MSEs
- Hybrid MSEs can manage internal supply chains

### 3. Performance Metrics
- Category-specific performance scores
- Growth rates by category
- Comparative analytics across categories

### 4. Reporting and Dashboards
- Category-specific reports
- Cross-category analysis
- Performance benchmarking

## Frontend Integration

### Updated API Configuration
The frontend API configuration has been updated to include:
- Category-specific endpoints
- Statistics endpoints
- Performance ranking endpoints
- Category summary endpoints

### New API Functions
```javascript
// Input MSEs
api.inputMses.list()
api.inputMses.create(data)
api.inputMses.update(id, data)
api.inputMses.delete(id)
api.inputMses.getStatistics()

// Output MSEs
api.outputMses.list()
api.outputMses.create(data)
api.outputMses.update(id, data)
api.outputMses.delete(id)
api.outputMses.getStatistics()

// Production MSEs
api.productionMses.list()
api.productionMses.create(data)
api.productionMses.update(id, data)
api.productionMses.delete(id)
api.productionMses.getStatistics()

// MSE Categories
api.mseCategories.list()
api.mseCategories.create(data)
api.mseCategories.update(id, data)
api.mseCategories.delete(id)
api.mseCategories.getSummary()
api.mseCategories.getPerformanceRanking()
```

## Benefits of the Category System

### 1. **Specialized Data Management**
- Each category has relevant fields and metrics
- Better data organization and retrieval
- Category-specific validation rules

### 2. **Targeted Analytics**
- Category-specific performance metrics
- Comparative analysis across categories
- Industry benchmarking capabilities

### 3. **Flexible Business Models**
- Support for hybrid businesses
- Scalable category system
- Easy addition of new categories

### 4. **Improved User Experience**
- Category-specific interfaces
- Relevant dashboards and reports
- Streamlined workflows

### 5. **Better Decision Making**
- Category-specific insights
- Performance tracking
- Strategic planning support

## Migration and Setup

### Database Migration
The new models have been created and migrated:
```bash
python manage.py makemigrations mses
python manage.py migrate
```

### Admin Interface
All new models are registered in the Django admin with:
- Proper field organization
- Search and filter capabilities
- Read-only timestamps
- Category-specific displays

### API Endpoints
All endpoints are available and documented:
- RESTful API design
- Proper authentication
- Comprehensive serializers
- Error handling

## Future Enhancements

### 1. **Advanced Analytics**
- Machine learning insights
- Predictive analytics
- Trend analysis

### 2. **Integration Features**
- Supply chain management
- Inventory tracking
- Financial integration

### 3. **Mobile Support**
- Mobile-optimized interfaces
- Offline capabilities
- Push notifications

### 4. **Reporting Engine**
- Custom report builder
- Scheduled reports
- Export capabilities

This category system provides a robust foundation for managing different types of MSEs with specialized features and analytics while maintaining flexibility for future enhancements.
