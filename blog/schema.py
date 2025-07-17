import graphene
from graphene import Mutation, InputObjectType, ObjectType
from graphene_django import DjangoObjectType
from django_filters import FilterSet, CharFilter,  DateTimeFilter
from datetime import  timezone
from blog.models import Post,Author,Category

class PostFilter(FilterSet):
    title_contains = CharFilter(field_name='title', lookup_expr='icontains')
    content_contains = CharFilter(field_name='content', lookup_expr='icontains')
    author_name = CharFilter(field_name='author__name', lookup_expr='icontains')
    category_name = CharFilter(field_name='categories__name', lookup_expr='icontains')
    created_after = DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = DateTimeFilter(field_name='created_at', lookup_expr='lte')
    class Meta:
        model = Post
        fields = ['status','featured','author','categories']

class AuthorFilter(FilterSet):
    name_contains = CharFilter(field_name='name', lookup_expr='icontains')
    email_contains = CharFilter(field_name='email', lookup_expr='icontains')

    class Meta:
        model = Author
        fields = ['name','email']

class CategoryFilter(FilterSet):
    name_contains = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Category
        fields = ['name']


#GraphQL Types
class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = '__all__'
        filter_fields = ['name']
        interfaces = (graphene.relay.Node,)

class AuthorType(DjangoObjectType):
    post_count = graphene.Int()

    class Meta:
        model = Author
        fields = '__all__'
        filter_fields = ['name','email']
        interfaces = (graphene.relay.Node,)

    def resolve_post_count(self,info):
        return self.posts.count()

class PostType(DjangoObjectType):
    is_published = graphene.Boolean()
    read_time = graphene.Int()

    class Meta:
        model = Post
        fields = '__all__'
        filter_fields = ['title','status','featured','author','categories']
        interfaces = (graphene.relay.Node,)

    def resolve_is_published(self,info):
        return self.status == 'published'
    def resolve_read_time(self,info):
        return len(self.content) // 200


class PostInput(InputObjectType):
    title = graphene.String(required=True)
    content = graphene.String(required=True)
    excerpt = graphene.String()
    author_id = graphene.ID(required=True)
    category_ids = graphene.List(graphene.ID)
    status = graphene.String()
    featured = graphene.Boolean()

class PostUpdateInput(InputObjectType):
    title = graphene.String()
    content = graphene.String()
    excerpt = graphene.String()
    author_id = graphene.ID()
    category_ids = graphene.List(graphene.ID)
    status = graphene.String()
    featured = graphene.Boolean()


class AuthorInput(InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    bio = graphene.String()
class CategoryInput(InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()

# Mutations
class CreatePost(Mutation):
    class Arguments:
        input = PostInput(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        try:
            author = Author.objects.get(pk=input.author_id)

            post = Post(
                title=input.title,
                content=input.content,
                excerpt=input.excerpt or '',
                author=author,
                status=input.status or 'draft',
                featured=input.featured or False
            )

            if input.status == 'published' and not post.published_at:
                post.published_at = timezone.now()

            post.save()

            # Add categories if provided
            if input.category_ids:
                categories = Category.objects.filter(id__in=input.category_ids)
                post.categories.set(categories)

            return CreatePost(post=post, success=True, errors=[])

        except Author.DoesNotExist:
            return CreatePost(post=None, success=False, errors=["Author not found"])
        except Exception as e:
            return CreatePost(post=None, success=False, errors=[str(e)])


class UpdatePost(Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = PostUpdateInput(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, input):
        try:
            post = Post.objects.get(pk=id)

            if input.title is not None:
                post.title = input.title
            if input.content is not None:
                post.content = input.content
            if input.excerpt is not None:
                post.excerpt = input.excerpt
            if input.status is not None:
                old_status = post.status
                post.status = input.status
                # Set published_at when status changes to published
                if input.status == 'published' and old_status != 'published':
                    post.published_at = timezone.now()
            if input.featured is not None:
                post.featured = input.featured

            if input.author_id is not None:
                author = Author.objects.get(pk=input.author_id)
                post.author = author

            post.save()

            # Update categories if provided
            if input.category_ids is not None:
                categories = Category.objects.filter(id__in=input.category_ids)
                post.categories.set(categories)

            return UpdatePost(post=post, success=True, errors=[])

        except Post.DoesNotExist:
            return UpdatePost(post=None, success=False, errors=["Post not found"])
        except Author.DoesNotExist:
            return UpdatePost(post=None, success=False, errors=["Author not found"])
        except Exception as e:
            return UpdatePost(post=None, success=False, errors=[str(e)])


class DeletePost(Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            post = Post.objects.get(pk=id)
            post.delete()
            return DeletePost(success=True, errors=[])
        except Post.DoesNotExist:
            return DeletePost(success=False, errors=["Post not found"])
        except Exception as e:
            return DeletePost(success=False, errors=[str(e)])


class CreateAuthor(Mutation):
    class Arguments:
        input = AuthorInput(required=True)

    author = graphene.Field(AuthorType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        try:
            author = Author(
                name=input.name,
                email=input.email,
                bio=input.bio or ''
            )
            author.save()
            return CreateAuthor(author=author, success=True, errors=[])
        except Exception as e:
            return CreateAuthor(author=None, success=False, errors=[str(e)])


class UpdateAuthor(Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = AuthorInput(required=True)

    author = graphene.Field(AuthorType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, input):
        try:
            author = Author.objects.get(pk=id)
            author.name = input.name
            author.email = input.email
            if input.bio is not None:
                author.bio = input.bio
            author.save()
            return UpdateAuthor(author=author, success=True, errors=[])
        except Author.DoesNotExist:
            return UpdateAuthor(author=None, success=False, errors=["Author not found"])
        except Exception as e:
            return UpdateAuthor(author=None, success=False, errors=[str(e)])


class DeleteAuthor(Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            author = Author.objects.get(pk=id)
            author.delete()
            return DeleteAuthor(success=True, errors=[])
        except Author.DoesNotExist:
            return DeleteAuthor(success=False, errors=["Author not found"])
        except Exception as e:
            return DeleteAuthor(success=False, errors=[str(e)])


class CreateCategory(graphene.Mutation):
    class Arguments:
        input = CategoryInput(required=True)

    category = graphene.Field(CategoryType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        try:
            category = Category(
                name=input.name,
                description=input.description or ''
            )
            category.save()
            return CreateCategory(category=category, success=True, errors=[])
        except Exception as e:
            return CreateCategory(category=None, success=False, errors=[str(e)])


class BulkDeletePosts(Mutation):
    class Arguments:
        ids = graphene.List(graphene.ID, required=True)

    deleted_count = graphene.Int()
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, ids):
        try:
            deleted_count, _ = Post.objects.filter(id__in=ids).delete()
            return BulkDeletePosts(
                deleted_count=deleted_count,
                success=True,
                errors=[]
            )
        except Exception as e:
            return BulkDeletePosts(
                deleted_count=0,
                success=False,
                errors=[str(e)]
            )


class PublishPost(Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        try:
            post = Post.objects.get(pk=id)
            post.status = 'published'
            post.published_at = timezone.now()
            post.save()
            return PublishPost(post=post, success=True, errors=[])
        except Post.DoesNotExist:
            return PublishPost(post=None, success=False, errors=["Post not found"])
        except Exception as e:
            return PublishPost(post=None, success=False, errors=[str(e)])


# Queries
class Query(ObjectType):
    # Basic queries
    posts = graphene.List(
        PostType,
        status=graphene.String(),
        featured=graphene.Boolean(),
        author_id=graphene.ID(),
        category_id=graphene.ID(),
        title_contains=graphene.String(),
        content_contains=graphene.String(),
        author_name=graphene.String(),
        created_after=graphene.DateTime(),
        created_before=graphene.DateTime(),
        limit=graphene.Int(),
        offset=graphene.Int(),
        order_by=graphene.String()
    )

    post = graphene.Field(PostType, id=graphene.ID(required=True))

    authors = graphene.List(
        AuthorType,
        name_contains=graphene.String(),
        email_contains=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )

    author = graphene.Field(AuthorType, id=graphene.ID(required=True))

    categories = graphene.List(
        CategoryType,
        name_contains=graphene.String(),
        limit=graphene.Int(),
        offset=graphene.Int()
    )

    category = graphene.Field(CategoryType, id=graphene.ID(required=True))

    # Analytics queries
    post_stats = graphene.Field(
        graphene.String,
        description="Returns JSON string with post statistics"
    )

    popular_posts = graphene.List(
        PostType,
        limit=graphene.Int(default_value=10),
        description="Returns most viewed posts"
    )

    recent_posts = graphene.List(
        PostType,
        limit=graphene.Int(default_value=10),
        description="Returns recently created posts"
    )

    def resolve_posts(self, info, **kwargs):
        qs = Post.objects.all()

        # Apply filters
        if kwargs.get('status'):
            qs = qs.filter(status=kwargs['status'])
        if kwargs.get('featured') is not None:
            qs = qs.filter(featured=kwargs['featured'])
        if kwargs.get('author_id'):
            qs = qs.filter(author_id=kwargs['author_id'])
        if kwargs.get('category_id'):
            qs = qs.filter(categories__id=kwargs['category_id'])
        if kwargs.get('title_contains'):
            qs = qs.filter(title__icontains=kwargs['title_contains'])
        if kwargs.get('content_contains'):
            qs = qs.filter(content__icontains=kwargs['content_contains'])
        if kwargs.get('author_name'):
            qs = qs.filter(author__name__icontains=kwargs['author_name'])
        if kwargs.get('created_after'):
            qs = qs.filter(created_at__gte=kwargs['created_after'])
        if kwargs.get('created_before'):
            qs = qs.filter(created_at__lte=kwargs['created_before'])
        order_by = kwargs.get('order_by', '-created_at')
        qs = qs.order_by(order_by)
        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit')

        qs = qs[offset:]
        if limit:
            qs = qs[:limit]

        return qs

    def resolve_post(self, info, id):
        try:
            post = Post.objects.get(pk=id)
            # Increment view count
            post.view_count += 1
            post.save()
            return post
        except Post.DoesNotExist:
            return None

    def resolve_authors(self, info, **kwargs):
        qs = Author.objects.all()

        if kwargs.get('name_contains'):
            qs = qs.filter(name__icontains=kwargs['name_contains'])
        if kwargs.get('email_contains'):
            qs = qs.filter(email__icontains=kwargs['email_contains'])

        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit')

        qs = qs[offset:]
        if limit:
            qs = qs[:limit]

        return qs

    def resolve_author(self, info, id):
        try:
            return Author.objects.get(pk=id)
        except Author.DoesNotExist:
            return None

    def resolve_categories(self, info, **kwargs):
        qs = Category.objects.all()

        if kwargs.get('name_contains'):
            qs = qs.filter(name__icontains=kwargs['name_contains'])

        offset = kwargs.get('offset', 0)
        limit = kwargs.get('limit')

        qs = qs[offset:]
        if limit:
            qs = qs[:limit]

        return qs

    def resolve_category(self, info, id):
        try:
            return Category.objects.get(pk=id)
        except Category.DoesNotExist:
            return None

    def resolve_post_stats(self, info):
        import json
        stats = {
            'total_posts': Post.objects.count(),
            'published_posts': Post.objects.filter(status='published').count(),
            'draft_posts': Post.objects.filter(status='draft').count(),
            'total_authors': Author.objects.count(),
            'total_categories': Category.objects.count(),
            'total_views': sum(Post.objects.values_list('view_count', flat=True)),
        }
        return json.dumps(stats)

    def resolve_popular_posts(self, info, limit=10):
        return Post.objects.filter(status='published').order_by('-view_count')[:limit]

    def resolve_recent_posts(self, info, limit=10):
        return Post.objects.filter(status='published').order_by('-created_at')[:limit]


# Mutations
class Mutation(graphene.ObjectType):
    # Post mutations
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    bulk_delete_posts = BulkDeletePosts.Field()
    publish_post = PublishPost.Field()

    # Author mutations
    create_author = CreateAuthor.Field()
    update_author = UpdateAuthor.Field()
    delete_author = DeleteAuthor.Field()

    # Category mutations
    create_category = CreateCategory.Field()