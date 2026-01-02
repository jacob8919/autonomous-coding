# Laravel + Blade (Alpine.js + Breeze) Stack

## Overview
Traditional Laravel with Blade templates and Alpine.js for interactivity.
Server-side rendering with progressive enhancement.
Includes Laravel Breeze for authentication scaffolding.

## Installation Commands
<installation_commands>
composer create-project laravel/laravel . --no-interaction
composer require laravel/breeze --dev
php artisan breeze:install blade --no-interaction
npm install
php artisan key:generate
php artisan migrate --force

# Install Laravel Boost for AI-powered development
composer require laravel/boost --dev
php artisan boost:install
</installation_commands>

## MCP Server Configuration
<mcp_servers>
{
    "laravel-boost": {
        "command": "php",
        "args": ["artisan", "boost:mcp"]
    }
}
</mcp_servers>

## Laravel Boost Tools
The Laravel Boost MCP server provides these tools to the autonomous agent:
- `search-docs` - Search Laravel documentation
- `list-artisan-commands` - List available artisan commands
- `tinker` - Interactive PHP shell for testing code
- `database-query` - Run database queries
- `get-absolute-url` - Get application URLs
- `browser-logs` - View browser/application logs

## Directory Structure
```
app/
├── Http/
│   ├── Controllers/      # Request handlers
│   ├── Middleware/       # HTTP middleware
│   └── Requests/         # Form request validation
├── Models/               # Eloquent models
├── View/
│   └── Components/       # Blade component classes
└── Providers/            # Service providers
bootstrap/
config/                   # Configuration files
database/
├── factories/            # Model factories for testing
├── migrations/           # Database migrations
└── seeders/              # Database seeders
public/                   # Public assets, index.php
resources/
├── views/
│   ├── components/       # Blade components
│   ├── layouts/          # Page layouts
│   ├── auth/             # Authentication views
│   └── *.blade.php       # Page templates
├── css/
│   └── app.css           # Tailwind CSS
└── js/
    └── app.js            # Alpine.js entry point
routes/
├── web.php               # Web routes
├── api.php               # API routes
└── auth.php              # Authentication routes
storage/                  # Logs, cache, sessions
tests/
├── Feature/              # Feature tests
└── Unit/                 # Unit tests
```

## Dev Server Commands
```bash
# Start Laravel backend (Terminal 1)
php artisan serve

# Start Vite for CSS/JS compilation (Terminal 2)
npm run dev
```

## Common Artisan Commands
```bash
# Database
php artisan migrate                    # Run migrations
php artisan migrate:fresh --seed       # Reset DB with seeders
php artisan db:seed                    # Run seeders

# Generate code
php artisan make:model Name -mcr       # Model + migration + controller + resource
php artisan make:controller NameController
php artisan make:migration create_table_name
php artisan make:request StoreNameRequest
php artisan make:middleware NameMiddleware
php artisan make:component ComponentName  # Blade component

# Cache & optimization
php artisan optimize:clear             # Clear all caches
php artisan config:cache               # Cache configuration
php artisan route:cache                # Cache routes
php artisan view:cache                 # Cache Blade views

# Testing
php artisan test                       # Run tests
php artisan test --filter=TestName     # Run specific test

# Maintenance
php artisan tinker                     # Interactive shell
php artisan route:list                 # List all routes
```

## Blade Syntax Reference
```php
{{-- Comments --}}
{{ $variable }}              {{-- Escaped output --}}
{!! $html !!}                {{-- Unescaped HTML --}}

@if($condition)
@elseif($other)
@else
@endif

@foreach($items as $item)
    {{ $item->name }}
@endforeach

@include('partials.header')
@extends('layouts.app')
@section('content')
@endsection
@yield('content')

{{-- Components --}}
<x-component-name :prop="$value" />
<x-slot:header>...</x-slot>
```

## Alpine.js Syntax Reference
```html
<div x-data="{ open: false }">
    <button @click="open = !open">Toggle</button>
    <div x-show="open" x-transition>Content</div>
</div>

<input x-model="search" />
<template x-for="item in items" :key="item.id">
    <span x-text="item.name"></span>
</template>
```

## Environment Notes
- Default database: SQLite (database/database.sqlite)
- Frontend port: 5173 (Vite for asset compilation)
- Backend port: 8000 (Laravel)
- Auth scaffolding included via Breeze (login, register, password reset)
- Tailwind CSS included for styling
- Alpine.js included for client-side interactivity
- Server-side rendering (SEO-friendly)
