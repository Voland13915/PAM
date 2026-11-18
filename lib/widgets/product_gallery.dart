import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/catalog_model.dart';
import 'product_image.dart';

class ProductGallery extends StatefulWidget {
  final int productId;
  final String category;
  final String fallbackUrl;
  final double height;

  const ProductGallery({
    super.key,
    required this.productId,
    required this.category,
    this.fallbackUrl = '',
    this.height = 260,
  });

  @override
  State<ProductGallery> createState() => _ProductGalleryState();
}

class _ProductGalleryState extends State<ProductGallery> {
  late final Future<List<String>> _images;
  final _controller = PageController();
  int _page = 0;

  @override
  void initState() {
    super.initState();
    _images = context.read<CatalogModel>().images(widget.productId);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _openFullscreen(List<String> images, int index) {
    Navigator.of(context).push(MaterialPageRoute<void>(
      fullscreenDialog: true,
      builder: (_) => _FullscreenGallery(images: images, initialIndex: index),
    ));
  }

  Widget _placeholder() => SizedBox(
        height: widget.height,
        child: Center(
          child: ProductImage(
            category: widget.category,
            imageUrl: widget.fallbackUrl,
            size: 160,
          ),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;

    return FutureBuilder<List<String>>(
      future: _images,
      builder: (context, snapshot) {
        final images = snapshot.data ?? const <String>[];
        if (images.isEmpty) return _placeholder();

        return Column(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: Container(
                height: widget.height,
                color: Colors.white,
                child: Stack(
                  children: [
                    PageView.builder(
                      controller: _controller,
                      itemCount: images.length,
                      onPageChanged: (page) => setState(() => _page = page),
                      itemBuilder: (context, index) => GestureDetector(
                        onTap: () => _openFullscreen(images, index),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Image.network(
                            images[index],
                            fit: BoxFit.contain,
                            loadingBuilder: (context, child, progress) =>
                                progress == null
                                    ? child
                                    : const Center(
                                        child: CircularProgressIndicator(
                                            strokeWidth: 2),
                                      ),
                            errorBuilder: (context, error, stackTrace) =>
                                Icon(ProductImage.iconFor(widget.category),
                                    size: 64, color: scheme.primary),
                          ),
                        ),
                      ),
                    ),
                    if (images.length > 1)
                      Positioned(
                        right: 12,
                        top: 12,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.black54,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            '${_page + 1} / ${images.length}',
                            style: const TextStyle(
                                color: Colors.white, fontSize: 12),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            if (images.length > 1) ...[
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var i = 0; i < images.length; i++)
                    AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      width: i == _page ? 16 : 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: i == _page
                            ? scheme.primary
                            : scheme.outlineVariant,
                        borderRadius: BorderRadius.circular(3),
                      ),
                    ),
                ],
              ),
            ],
          ],
        );
      },
    );
  }
}

class _FullscreenGallery extends StatefulWidget {
  final List<String> images;
  final int initialIndex;

  const _FullscreenGallery({required this.images, required this.initialIndex});

  @override
  State<_FullscreenGallery> createState() => _FullscreenGalleryState();
}

class _FullscreenGalleryState extends State<_FullscreenGallery> {
  late final PageController _controller =
      PageController(initialPage: widget.initialIndex);
  late int _page = widget.initialIndex;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        backgroundColor: Colors.white,
        title: Text('${_page + 1} / ${widget.images.length}'),
      ),
      body: PageView.builder(
        controller: _controller,
        itemCount: widget.images.length,
        onPageChanged: (page) => setState(() => _page = page),
        itemBuilder: (context, index) => InteractiveViewer(
          maxScale: 4,
          child: Center(
            child: Image.network(widget.images[index], fit: BoxFit.contain),
          ),
        ),
      ),
    );
  }
}
