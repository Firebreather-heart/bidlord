from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    Home page view that shows the BidLord landing page
    """
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title': 'BidLord - Bidding Platform API',
            'description': 'A comprehensive bidding platform API built with Django REST Framework',
        })
        return context


class WebSocketDocsView(TemplateView):
    """
    Renders the dedicated documentation page for WebSocket APIs.
    """
    template_name = 'websocket_docs.html'
    extra_context = {
        'title': 'WebSocket API Documentation - BidLord',
        'description': 'Real-time auction updates via WebSocket API',
    }