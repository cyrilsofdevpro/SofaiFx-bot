/**
 * Lazy Loading Module
 * Defers initialization of expensive components until they're visible
 */

class LazyLoader {
    constructor() {
        this.components = new Map();
        this.initialized = new Set();
        this.observer = null;
        this.initObserver();
    }

    /**
     * Initialize Intersection Observer for visibility detection
     */
    initObserver() {
        const options = {
            root: null,
            rootMargin: '100px',  // Start loading 100px before component becomes visible
            threshold: 0.01
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const componentId = entry.target.id;
                    this.loadComponent(componentId);
                }
            });
        }, options);
    }

    /**
     * Register a component for lazy loading
     */
    register(componentId, initFn, containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) {
            console.warn(`⚠️ Container not found for lazy component: ${componentId}`);
            return;
        }

        this.components.set(componentId, {
            initFn,
            container,
            initialized: false
        });

        // Start observing
        this.observer.observe(container);
        console.log(`📦 Registered lazy component: ${componentId}`);
    }

    /**
     * Load component if not already loaded
     */
    loadComponent(componentId) {
        if (this.initialized.has(componentId)) {
            console.log(`✓ Component already initialized: ${componentId}`);
            return;
        }

        const component = this.components.get(componentId);
        if (!component) return;

        console.log(`🚀 Initializing lazy component: ${componentId}`);
        
        try {
            component.initFn();
            this.initialized.add(componentId);
            
            // Stop observing after initialization
            this.observer.unobserve(component.container);
            console.log(`✅ Lazy loaded: ${componentId}`);
        } catch (err) {
            console.error(`❌ Error initializing ${componentId}:`, err);
        }
    }

    /**
     * Manually trigger loading of a component
     */
    forceLoad(componentId) {
        this.loadComponent(componentId);
    }

    /**
     * Check if component is loaded
     */
    isLoaded(componentId) {
        return this.initialized.has(componentId);
    }

    /**
     * Get statistics
     */
    getStats() {
        return {
            registered: this.components.size,
            initialized: this.initialized.size,
            pending: this.components.size - this.initialized.size
        };
    }
}

window.lazyLoader = new LazyLoader();
