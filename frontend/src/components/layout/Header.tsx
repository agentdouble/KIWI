import { UserAvatar } from './UserAvatar';

export const Header = () => {
  return (
    <header className="absolute top-8 right-6 z-10">
      <UserAvatar />
    </header>
  );
}