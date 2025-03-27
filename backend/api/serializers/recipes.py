from rest_framework import serializers
from recipes.models import Recipe, Tag, Ingredient, RecipeIngredient
from api.serializers.users import UserProfileSerializer
from recipes.models import Favorite, ShoppingCart
from drf_extra_fields.fields import Base64ImageField
from foodgram.constants import RECIPE_NAME_MAX_LENGTH


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    author = UserProfileSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_tags(self, obj):
        from api.serializers.recipes import TagSerializer
        return TagSerializer(obj.tags.all(), many=True).data
    
    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Нужно выбрать хотя бы один тег.')
        return value


    def get_ingredients(self, obj):
        ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return IngredientAmountSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated and
            obj.favorited_by.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return (
            user.is_authenticated and
            obj.in_carts.filter(user=user).exists()
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        allow_empty=False
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=1)
    name = serializers.CharField(max_length=RECIPE_NAME_MAX_LENGTH, required=True)
    text = serializers.CharField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image', 'name',
            'text', 'cooking_time'
        )

    def validate_ingredients(self, value):
        seen = set()
        for item in value:
            ingredient_id = item.get('id')
            if ingredient_id is None:
                raise serializers.ValidationError('Каждый ингредиент должен иметь id.')
            if ingredient_id in seen:
                raise serializers.ValidationError('Ингредиенты не должны повторяться.')
            seen.add(ingredient_id)
            amount = item.get('amount')
            if amount is None or not isinstance(amount, (int, str)) or int(amount) < 1:
                raise serializers.ValidationError('Количество ингредиентов должно быть не меньше одного.')
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id={ingredient_id} не существует.'
                )
        return value

    def validate_tags(self, value):
        # value — это список объектов Tag, а не ID
        seen = set()
        for tag in value:
            tag_id = tag.id  # Получаем ID из объекта Tag
            if tag_id in seen:
                raise serializers.ValidationError('Теги не должны повторяться.')
            seen.add(tag_id)
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError('Обязательно надо добавить картинку.')
        return value

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Название рецепта не может быть пустым.')
        if len(value) > RECIPE_NAME_MAX_LENGTH:
            raise serializers.ValidationError(
                f'Название не должно превышать {RECIPE_NAME_MAX_LENGTH} символов.'
            )
        return value

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError('Описание рецепта не может быть пустым.')
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError('Время приготовления должно быть не меньше 1 минуты.')
        return value

    def create_ingredients(self, recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=item['id']),
                amount=item['amount']
            ) for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            author=self.context['request'].user,
            **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredients.clear()
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self.create_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
