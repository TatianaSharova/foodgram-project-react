class FollowSerializer(serializers.ModelSerializer):
    '''Serializer для оформления подписки.'''
    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.ReadOnlyField(source='following.recipes.count')

    class Meta:
        model = Follow
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following')
            )
        ]

    def validate_following(self, data):
        if Follow.objects.filter(
                following=data.get('following'),
                user=self.context['request'].user).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя!'
        )
        if self.context['request'].user != data.get('following'):
            return data
        raise serializers.ValidationError(
            'Нельзя подписаться на себя!'
        )

    def get_recipes(self, obj):
        """Получение списка рецептов автора."""

        author_recipes = obj.following.recipes.all()

        if author_recipes:
            serializer = RecipeShortSerializer(
                author_recipes,
                context={"request": self.context.get("request")},
                many=True,
            )
            return serializer.data

        return []

    def get_recipes_count(self, obj):
        """Количество рецептов автора."""
        return Recipe.objects.filter(author=obj.id).count()

    
    def get_is_subscribed(self, obj):
        '''Проверка на подписку.'''
        user_id = self.context.get("request").user.id
        return Follow.objects.filter(
            user=user_id, following=obj.id
        ).exists()