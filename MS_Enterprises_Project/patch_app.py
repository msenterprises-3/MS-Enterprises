import re

def patch_app_py():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Patch api_admin_products POST
    post_search = """        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Product created successfully!', 'id': p_id})"""
        
    post_replace = """        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        try:
            from supabase_db import supabase_client
            for idx, img in enumerate(data.get('images', [])):
                import uuid
                img_id = str(uuid.uuid4().int)[:8]
                supabase_client.table('product_images').insert({
                    'id': int(img_id),
                    'product_id': int(p_id),
                    'image_url': img,
                    'display_order': idx
                }).execute()
            for idx, var in enumerate(data.get('variants', [])):
                import uuid
                var_id = str(uuid.uuid4().int)[:8]
                supabase_client.table('product_variants').insert({
                    'id': int(var_id),
                    'product_id': int(p_id),
                    'variant_name': var.get('name', f'Variant {idx}'),
                    'price_adjustment': float(var.get('price_adjustment', 0)),
                    'stock': int(var.get('stock', 0))
                }).execute()
        except Exception as e:
            print(f"Failed to add images/variants natively: {e}")
            
        touch_catalogue_update()
        from firebase_db import product_announcer
        product_announcer.announce('update')
        return jsonify({'success': True, 'message': 'Product created successfully!', 'id': p_id})"""

    content = content.replace(post_search, post_replace)
    
    # 2. Patch api_admin_products PUT
    put_search = """        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Product updated successfully!'})"""
        
    put_replace = """        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        try:
            from supabase_db import supabase_client
            supabase_client.table('product_images').delete().eq('product_id', int(p_id)).execute()
            supabase_client.table('product_variants').delete().eq('product_id', int(p_id)).execute()
            for idx, img in enumerate(data.get('images', [])):
                import uuid
                img_id = str(uuid.uuid4().int)[:8]
                supabase_client.table('product_images').insert({
                    'id': int(img_id),
                    'product_id': int(p_id),
                    'image_url': img,
                    'display_order': idx
                }).execute()
            for idx, var in enumerate(data.get('variants', [])):
                import uuid
                var_id = str(uuid.uuid4().int)[:8]
                supabase_client.table('product_variants').insert({
                    'id': int(var_id),
                    'product_id': int(p_id),
                    'variant_name': var.get('name', f'Variant {idx}'),
                    'price_adjustment': float(var.get('price_adjustment', 0)),
                    'stock': int(var.get('stock', 0))
                }).execute()
        except Exception as e:
            print(f"Failed to update images/variants natively: {e}")
            
        touch_catalogue_update()
        from firebase_db import product_announcer
        product_announcer.announce('update')
        return jsonify({'success': True, 'message': 'Product updated successfully!'})"""

    content = content.replace(put_search, put_replace)

    # 3. Patch api_admin_products DELETE
    del_search = """        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        touch_catalogue_update()
        return jsonify({'success': True, 'message': 'Product deleted successfully!'})"""
        
    del_replace = """        except Exception as e:
            return jsonify({'success': False, 'message': f'Database Error: {str(e)}'}), 500
            
        touch_catalogue_update()
        from firebase_db import product_announcer
        product_announcer.announce('update')
        return jsonify({'success': True, 'message': 'Product deleted successfully!'})"""

    content = content.replace(del_search, del_replace)
    
    # 4. Patch api_cart routes
    cart_add_search = """        batch.commit()
    
    return jsonify({'success': True, 'message': 'Added to cart.'})"""
    
    cart_add_replace = """        batch.commit()
    
    from firebase_db import product_announcer
    product_announcer.announce('update')
    return jsonify({'success': True, 'message': 'Added to cart.'})"""
    content = content.replace(cart_add_search, cart_add_replace)
    
    cart_upd_search = """        return jsonify({'success': False, 'message': 'Item not found in cart.'}), 404
        
    return jsonify({'success': True, 'message': 'Cart updated.'})"""
    cart_upd_replace = """        return jsonify({'success': False, 'message': 'Item not found in cart.'}), 404
        
    from firebase_db import product_announcer
    product_announcer.announce('update')
    return jsonify({'success': True, 'message': 'Cart updated.'})"""
    content = content.replace(cart_upd_search, cart_upd_replace)

    cart_rem_search = """        return jsonify({'success': False, 'message': 'Item not found in cart.'}), 404
        
    return jsonify({'success': True, 'message': 'Item removed from cart.'})"""
    cart_rem_replace = """        return jsonify({'success': False, 'message': 'Item not found in cart.'}), 404
        
    from firebase_db import product_announcer
    product_announcer.announce('update')
    return jsonify({'success': True, 'message': 'Item removed from cart.'})"""
    content = content.replace(cart_rem_search, cart_rem_replace)

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Patched app.py successfully!")

if __name__ == '__main__':
    patch_app_py()
