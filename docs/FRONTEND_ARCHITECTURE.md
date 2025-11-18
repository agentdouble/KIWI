# Architecture Frontend - FoyerGPT

## Vue d'ensemble

Le frontend de FoyerGPT est une application React moderne construite avec TypeScript. L'architecture suit les meilleures pratiques React avec une séparation claire des responsabilités et une gestion d'état robuste.

## Stack technologique

- **Framework** : React 19.1.0
- **Langage** : TypeScript 5.8
- **Build Tool** : Vite 7.0
- **Styling** : Tailwind CSS 3.4
- **État global** : Zustand 5.0
- **État serveur** : TanStack React Query 5.81
- **Routing** : React Router 7.6
- **UI Components** : Radix UI
- **HTTP Client** : Axios
- **WebSocket** : Socket.IO Client

## Structure du projet

```
frontend/
├── src/
│   ├── components/             # Composants réutilisables
│   │   ├── agents/            # Composants agents
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentForm.tsx
│   │   │   ├── AgentList.tsx
│   │   │   └── AgentSelector.tsx
│   │   │
│   │   ├── auth/              # Composants authentification
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   │
│   │   ├── chat/              # Composants chat
│   │   │   ├── ChatContainer.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── Message.tsx
│   │   │   ├── WelcomeScreen.tsx
│   │   │   └── TypingIndicator.tsx
│   │   │
│   │   ├── documents/         # Composants documents
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── DocumentUploadStatus.tsx
│   │   │
│   │   ├── layout/            # Composants mise en page
│   │   │   ├── MainLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── UserAvatar.tsx
│   │   │
│   │   └── ui/                # Composants UI de base
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── dialog.tsx
│   │       ├── input.tsx
│   │       ├── label.tsx
│   │       ├── select.tsx
│   │       ├── textarea.tsx
│   │       └── toast.tsx
│   │
│   ├── hooks/                  # React hooks personnalisés
│   │   ├── api/               # Hooks API
│   │   │   ├── useAgents.ts
│   │   │   ├── useChats.ts
│   │   │   ├── useMessages.ts
│   │   │   └── useSession.ts
│   │   │
│   │   ├── useApiError.ts
│   │   ├── useBackendConnection.ts
│   │   ├── useKeyboardShortcuts.ts
│   │   ├── useRealtimeMessages.ts
│   │   └── useTheme.ts
│   │
│   ├── lib/                    # Bibliothèques et utilitaires
│   │   ├── api/               # Configuration API
│   │   │   ├── config.ts
│   │   │   ├── index.ts
│   │   │   └── services/
│   │   │
│   │   ├── socket/            # Configuration WebSocket
│   │   │   ├── config.ts
│   │   │   └── types.ts
│   │   │
│   │   └── utils.ts           # Utilitaires généraux
│   │
│   ├── pages/                  # Pages de l'application
│   │   ├── Chat.tsx           # Page de chat principale
│   │   ├── Login.tsx          # Page de connexion
│   │   ├── Register.tsx       # Page d'inscription
│   │   ├── Marketplace.tsx    # Marketplace d'agents
│   │   ├── MyGPTs.tsx         # Agents de l'utilisateur
│   │   └── CreateAgent.tsx    # Création d'agent
│   │
│   ├── providers/              # Context providers
│   │   ├── BackendProvider.tsx
│   │   ├── SocketProvider.tsx
│   │   └── ToastProvider.tsx
│   │
│   ├── stores/                 # État global (Zustand)
│   │   ├── authStore.ts       # État authentification
│   │   ├── chatStore.ts       # État conversations
│   │   ├── agentStore.ts      # État agents
│   │   └── sessionStore.ts    # État sessions
│   │
│   ├── types/                  # Types TypeScript
│   │   ├── agent.ts
│   │   ├── api.d.ts
│   │   ├── chat.d.ts
│   │   └── index.ts
│   │
│   ├── App.tsx                # Composant racine
│   ├── main.tsx               # Point d'entrée
│   └── index.css              # Styles globaux
│
├── public/                     # Assets statiques
├── index.html                  # Template HTML
├── package.json                # Dépendances
├── tsconfig.json               # Configuration TypeScript
├── vite.config.ts              # Configuration Vite
└── tailwind.config.js          # Configuration Tailwind
```

## Composants principaux

### App.tsx - Composant racine

```tsx
function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BackendInitializer>
          <SocketProvider>
            <ToastProvider>
              <Router>
                <Routes>
                  {/* Routes publiques */}
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  
                  {/* Routes protégées */}
                  <Route element={<ProtectedRoute />}>
                    <Route element={<MainLayout />}>
                      <Route path="/" element={<Chat />} />
                      <Route path="/chat/:chatId" element={<Chat />} />
                      <Route path="/marketplace" element={<Marketplace />} />
                      <Route path="/my-gpts" element={<MyGPTs />} />
                      <Route path="/agents/new" element={<CreateAgent />} />
                    </Route>
                  </Route>
                </Routes>
              </Router>
            </ToastProvider>
          </SocketProvider>
        </BackendInitializer>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
```

### ChatContainer - Logique principale du chat

```tsx
interface ChatContainerProps {
  chatId?: string;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ chatId }) => {
  const { messages, sendMessage, isLoading } = useChat(chatId);
  const { selectedAgent } = useAgentStore();
  
  const handleSendMessage = async (content: string, files?: File[]) => {
    if (!selectedAgent) return;
    
    await sendMessage({
      content,
      files,
      agentId: selectedAgent.id
    });
  };
  
  return (
    <div className="flex flex-col h-full">
      {messages.length === 0 ? (
        <WelcomeScreen agent={selectedAgent} />
      ) : (
        <MessageList messages={messages} />
      )}
      <ChatInput 
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
    </div>
  );
};
```

## Gestion d'état

### Zustand - État client

```typescript
// authStore.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (email, password) => {
    const response = await authApi.login(email, password);
    set({
      user: response.user,
      token: response.token,
      isAuthenticated: true
    });
    localStorage.setItem('token', response.token);
  },
  
  logout: () => {
    set({ user: null, token: null, isAuthenticated: false });
    localStorage.removeItem('token');
  },
  
  updateUser: (user) => set({ user })
}));
```

### React Query - État serveur

```typescript
// useChats.ts
export const useChats = () => {
  const queryClient = useQueryClient();
  
  const chatsQuery = useQuery({
    queryKey: ['chats'],
    queryFn: chatApi.getChats,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
  
  const createChatMutation = useMutation({
    mutationFn: chatApi.createChat,
    onSuccess: (newChat) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] });
      queryClient.setQueryData(['chat', newChat.id], newChat);
    }
  });
  
  return {
    chats: chatsQuery.data ?? [],
    isLoading: chatsQuery.isLoading,
    createChat: createChatMutation.mutate
  };
};
```

## Configuration API

### Axios avec intercepteurs

```typescript
// api/config.ts
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8061/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Intercepteur pour ajouter le token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  const sessionId = sessionStorage.getItem('sessionId');
  if (sessionId) {
    config.headers['X-Session-ID'] = sessionId;
  }
  
  return config;
});

// Intercepteur pour gérer les erreurs
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Routing et navigation

### Protected Routes

```tsx
const ProtectedRoute: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return <Outlet />;
};
```

### Navigation avec React Router

```tsx
// Navigation programmatique
const navigate = useNavigate();

// Après création d'un chat
const handleCreateChat = async () => {
  const newChat = await createChat({ agentId });
  navigate(`/chat/${newChat.id}`);
};

// Navigation avec state
navigate('/agents/new', { state: { fromMarketplace: true } });
```

## Composants UI réutilisables

### Design System avec Radix UI

```tsx
// components/ui/button.tsx
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
```

### Composants composés

```tsx
// Dialog composé
<Dialog>
  <DialogTrigger asChild>
    <Button>Créer un agent</Button>
  </DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Nouvel Agent IA</DialogTitle>
      <DialogDescription>
        Créez un agent personnalisé avec ses propres capacités
      </DialogDescription>
    </DialogHeader>
    <AgentForm onSubmit={handleCreateAgent} />
  </DialogContent>
</Dialog>
```

## Hooks personnalisés

### useRealtimeMessages

```typescript
export const useRealtimeMessages = (chatId: string) => {
  const queryClient = useQueryClient();
  const socket = useSocket();
  
  useEffect(() => {
    if (!socket || !chatId) return;
    
    socket.emit('join_chat', { chatId });
    
    const handleNewMessage = (message: Message) => {
      queryClient.setQueryData<Message[]>(
        ['messages', chatId],
        (old = []) => [...old, message]
      );
    };
    
    socket.on('new_message', handleNewMessage);
    
    return () => {
      socket.off('new_message', handleNewMessage);
      socket.emit('leave_chat', { chatId });
    };
  }, [socket, chatId, queryClient]);
};
```

### useKeyboardShortcuts

```typescript
export const useKeyboardShortcuts = () => {
  const navigate = useNavigate();
  
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K pour nouvelle conversation
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        navigate('/');
      }
      
      // Cmd/Ctrl + , pour paramètres
      if ((e.metaKey || e.ctrlKey) && e.key === ',') {
        e.preventDefault();
        navigate('/settings');
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [navigate]);
};
```

## Optimisations de performance

### Code Splitting

```typescript
// Lazy loading des pages
const Marketplace = lazy(() => import('./pages/Marketplace'));
const MyGPTs = lazy(() => import('./pages/MyGPTs'));

// Utilisation avec Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/marketplace" element={<Marketplace />} />
    <Route path="/my-gpts" element={<MyGPTs />} />
  </Routes>
</Suspense>
```

### Memoization

```typescript
// Composant mémorisé
const Message = React.memo(({ message, isLastMessage }: MessageProps) => {
  return (
    <div className={cn(
      'flex gap-3 p-4',
      message.role === 'user' ? 'bg-gray-50' : 'bg-white'
    )}>
      {/* Contenu du message */}
    </div>
  );
}, (prevProps, nextProps) => {
  return prevProps.message.id === nextProps.message.id &&
         prevProps.isLastMessage === nextProps.isLastMessage;
});

// Hook mémorisé
const expensiveComputation = useMemo(() => {
  return messages.filter(m => m.role === 'assistant').length;
}, [messages]);
```

### Optimistic Updates

```typescript
const sendMessageMutation = useMutation({
  mutationFn: messageApi.sendMessage,
  onMutate: async (newMessage) => {
    // Annuler les requêtes en cours
    await queryClient.cancelQueries(['messages', chatId]);
    
    // Snapshot des données actuelles
    const previousMessages = queryClient.getQueryData(['messages', chatId]);
    
    // Mise à jour optimiste
    queryClient.setQueryData(['messages', chatId], (old: Message[] = []) => [
      ...old,
      { ...newMessage, id: 'temp-' + Date.now(), status: 'sending' }
    ]);
    
    return { previousMessages };
  },
  onError: (err, newMessage, context) => {
    // Rollback en cas d'erreur
    queryClient.setQueryData(['messages', chatId], context.previousMessages);
  },
  onSettled: () => {
    // Refetch pour synchroniser
    queryClient.invalidateQueries(['messages', chatId]);
  }
});
```

## Styling avec Tailwind CSS

### Configuration personnalisée

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      }
    }
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
  ]
};
```

### Composants stylisés

```tsx
// Utilisation de class variance authority
const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary-600 text-white hover:bg-primary-700',
        destructive: 'bg-red-600 text-white hover:bg-red-700',
        outline: 'border border-gray-300 bg-white hover:bg-gray-50',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    }
  }
);
```

## Tests

### Configuration Jest + React Testing Library

```typescript
// setupTests.ts
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Exemple de test

```typescript
// ChatInput.test.tsx
describe('ChatInput', () => {
  it('should send message on submit', async () => {
    const onSendMessage = jest.fn();
    const { getByPlaceholderText, getByRole } = render(
      <ChatInput onSendMessage={onSendMessage} />
    );
    
    const input = getByPlaceholderText('Tapez votre message...');
    const button = getByRole('button', { name: /envoyer/i });
    
    await userEvent.type(input, 'Hello world');
    await userEvent.click(button);
    
    expect(onSendMessage).toHaveBeenCalledWith('Hello world', []);
  });
});
```

## Build et déploiement

### Configuration Vite

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8060,
    proxy: {
      '/api': {
        target: 'http://localhost:8061',
        changeOrigin: true,
      },
      '/ws': {
        target: 'http://localhost:8061',
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        }
      }
    }
  }
});
```

### Scripts de build

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "jest",
    "lint": "eslint src --ext ts,tsx",
    "type-check": "tsc --noEmit"
  }
}
```