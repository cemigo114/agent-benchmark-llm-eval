"""Retail domain API tools for agent evaluation."""

import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import random
import json

from ...utils.logging import get_logger

logger = get_logger(__name__)


class ProductDatabase:
    """Mock product database for retail evaluation."""
    
    def __init__(self):
        self.products = {
            "prod_001": {
                "id": "prod_001",
                "name": "Wireless Headphones",
                "category": "Electronics",
                "price": 199.99,
                "in_stock": True,
                "quantity": 50,
                "description": "High-quality wireless headphones with noise cancellation"
            },
            "prod_002": {
                "id": "prod_002", 
                "name": "Running Shoes",
                "category": "Footwear",
                "price": 129.99,
                "in_stock": True,
                "quantity": 25,
                "description": "Comfortable running shoes for all terrains"
            },
            "prod_003": {
                "id": "prod_003",
                "name": "Coffee Maker",
                "category": "Appliances", 
                "price": 89.99,
                "in_stock": False,
                "quantity": 0,
                "description": "Automatic drip coffee maker with programmable timer"
            },
            "prod_004": {
                "id": "prod_004",
                "name": "Yoga Mat",
                "category": "Fitness",
                "price": 39.99,
                "in_stock": True,
                "quantity": 100,
                "description": "Non-slip exercise yoga mat, 6mm thick"
            },
            "prod_005": {
                "id": "prod_005",
                "name": "Smartphone",
                "category": "Electronics",
                "price": 699.99,
                "in_stock": True,
                "quantity": 15,
                "description": "Latest smartphone with 128GB storage"
            }
        }
        
        self.orders = {}
        self.order_counter = 1
        
    def search_products(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search products by name or description."""
        results = []
        query_lower = query.lower()
        
        for product in self.products.values():
            if category and product["category"].lower() != category.lower():
                continue
                
            if (query_lower in product["name"].lower() or 
                query_lower in product["description"].lower() or
                query_lower in product["category"].lower()):
                results.append(product.copy())
        
        return results
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID."""
        return self.products.get(product_id, {}).copy() if product_id in self.products else None
    
    def check_stock(self, product_id: str) -> Dict[str, Any]:
        """Check product stock levels."""
        product = self.products.get(product_id)
        if not product:
            return {"error": "Product not found"}
        
        return {
            "product_id": product_id,
            "in_stock": product["in_stock"],
            "quantity": product["quantity"],
            "name": product["name"]
        }
    
    def create_order(self, customer_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new order."""
        order_id = f"order_{self.order_counter:04d}"
        self.order_counter += 1
        
        # Validate and calculate total
        order_items = []
        total_price = 0
        
        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 1)
            
            product = self.products.get(product_id)
            if not product:
                return {"error": f"Product {product_id} not found"}
            
            if not product["in_stock"] or product["quantity"] < quantity:
                return {"error": f"Insufficient stock for {product['name']}"}
            
            item_total = product["price"] * quantity
            order_items.append({
                "product_id": product_id,
                "product_name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "total_price": item_total
            })
            total_price += item_total
            
            # Update stock
            self.products[product_id]["quantity"] -= quantity
            if self.products[product_id]["quantity"] == 0:
                self.products[product_id]["in_stock"] = False
        
        # Create order
        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "items": order_items,
            "total_price": total_price,
            "status": "confirmed",
            "created_at": datetime.now().isoformat(),
            "estimated_delivery": (datetime.now() + timedelta(days=3)).isoformat()
        }
        
        self.orders[order_id] = order
        return order
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by ID."""
        return self.orders.get(order_id, {}).copy() if order_id in self.orders else None


# Global database instance
product_db = ProductDatabase()


class RetailTools:
    """Retail domain API tools."""
    
    @staticmethod
    async def search_products(query: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Search for products in the catalog."""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        logger.info(f"Searching products: query='{query}', category='{category}'")
        
        try:
            results = product_db.search_products(query, category)
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_product_details(product_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific product."""
        await asyncio.sleep(0.1)
        
        logger.info(f"Getting product details: {product_id}")
        
        try:
            product = product_db.get_product(product_id)
            if product:
                return {"success": True, "product": product}
            else:
                return {"success": False, "error": "Product not found"}
        except Exception as e:
            logger.error(f"Error getting product details: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def check_inventory(product_id: str) -> Dict[str, Any]:
        """Check inventory levels for a product."""
        await asyncio.sleep(0.1)
        
        logger.info(f"Checking inventory: {product_id}")
        
        try:
            stock_info = product_db.check_stock(product_id)
            return {"success": True, "stock": stock_info}
        except Exception as e:
            logger.error(f"Error checking inventory: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def place_order(customer_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Place an order for multiple items."""
        await asyncio.sleep(0.2)
        
        logger.info(f"Placing order: customer={customer_id}, items={len(items)}")
        
        try:
            order = product_db.create_order(customer_id, items)
            if "error" in order:
                return {"success": False, "error": order["error"]}
            else:
                return {"success": True, "order": order}
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def get_order_status(order_id: str) -> Dict[str, Any]:
        """Get the status of an existing order."""
        await asyncio.sleep(0.1)
        
        logger.info(f"Getting order status: {order_id}")
        
        try:
            order = product_db.get_order(order_id)
            if order:
                return {"success": True, "order": order}
            else:
                return {"success": False, "error": "Order not found"}
        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def apply_discount(order_id: str, discount_code: str) -> Dict[str, Any]:
        """Apply a discount code to an order."""
        await asyncio.sleep(0.1)
        
        logger.info(f"Applying discount: order={order_id}, code={discount_code}")
        
        # Simulate discount validation
        valid_codes = {
            "SAVE10": 0.10,
            "WELCOME20": 0.20,
            "STUDENT15": 0.15
        }
        
        try:
            order = product_db.get_order(order_id)
            if not order:
                return {"success": False, "error": "Order not found"}
            
            if discount_code not in valid_codes:
                return {"success": False, "error": "Invalid discount code"}
            
            discount_percent = valid_codes[discount_code]
            original_total = order["total_price"]
            discount_amount = original_total * discount_percent
            new_total = original_total - discount_amount
            
            # Update order (in real system, would save to database)
            order["discount_code"] = discount_code
            order["discount_amount"] = discount_amount
            order["total_price"] = new_total
            product_db.orders[order_id] = order
            
            return {
                "success": True,
                "discount_applied": {
                    "code": discount_code,
                    "discount_percent": discount_percent * 100,
                    "discount_amount": discount_amount,
                    "original_total": original_total,
                    "new_total": new_total
                }
            }
        except Exception as e:
            logger.error(f"Error applying discount: {e}")
            return {"success": False, "error": str(e)}


def get_retail_tools() -> List[Dict[str, Any]]:
    """Get the list of available retail tools for agents."""
    return [
        {
            "name": "search_products",
            "description": "Search for products in the catalog by name, description, or category",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for product name or description"
                    },
                    "category": {
                        "type": "string", 
                        "description": "Optional category filter (Electronics, Footwear, Appliances, Fitness)"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_product_details",
            "description": "Get detailed information about a specific product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Unique product identifier"
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "check_inventory",
            "description": "Check inventory levels and availability for a product",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string", 
                        "description": "Unique product identifier"
                    }
                },
                "required": ["product_id"]
            }
        },
        {
            "name": "place_order",
            "description": "Place an order for one or more items",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "Unique customer identifier"
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1}
                            },
                            "required": ["product_id", "quantity"]
                        },
                        "description": "List of items to order"
                    }
                },
                "required": ["customer_id", "items"]
            }
        },
        {
            "name": "get_order_status",
            "description": "Get the status and details of an existing order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Unique order identifier"
                    }
                },
                "required": ["order_id"]
            }
        },
        {
            "name": "apply_discount",
            "description": "Apply a discount code to an existing order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Unique order identifier"
                    },
                    "discount_code": {
                        "type": "string",
                        "description": "Discount code to apply"
                    }
                },
                "required": ["order_id", "discount_code"]
            }
        }
    ]