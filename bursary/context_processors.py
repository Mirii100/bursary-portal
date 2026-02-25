from django.utils import timezone

def time_based_greeting(request):
    """
    Returns a greeting based on the current server time.
    """
    now = timezone.now().astimezone(timezone.get_current_timezone())
    hour = now.hour
    
    if hour < 12:
        greeting = "Good Morning"
    elif 12 <= hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
        
    return {
        'time_greeting': greeting
    }
