INSERT INTO products (pid, name, winery, varietal, year, photo_url, price_list, promo_type, promo_value, promo_valid_from, promo_valid_to, stock_status, description)
VALUES
('G7AKJ3H9XY1', 'Malbec Reserva 2021', 'Bodega X', 'Malbec', 2021, NULL, 9200.00, 'percent', 15, NOW() - INTERVAL '1 day', NOW() + INTERVAL '7 days', 'available', 'Intenso y frutado; ideal para asado.'),
('K2LMN8PQ45Z', 'Cabernet Clásico', 'Bodega Y', 'Cabernet Sauvignon', 2020, NULL, 8100.00, 'two_for', 14000.00, NOW() - INTERVAL '2 days', NOW() + INTERVAL '5 days', 'available', 'Estructura media, final especiado.'),
('Z9QR5TU7VW3', 'Blend Andino', 'Bodega Z', 'Blend', 2019, NULL, 10500.00, NULL, NULL, NULL, NULL, 'low', 'Corte equilibrado, buena relación precio-calidad.');
