def calculate_size(initialized_size: int, initialized_screen_s: int, size: int):
    '''
    Ekran boyutuna göre boyut hesaplar. Dinamik boyut gerektiren objeler için.
    '''
    calculated = int(initialized_size * (size / initialized_screen_s))
    return calculated
