"""
Test suite for FeelSync games functionality.
Tests the game logic, scoring, achievements, and user interactions.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the game logic since it's primarily JavaScript-based
class MockEmotionalBalanceGame:
    """Mock class representing the JavaScript game logic for testing."""
    
    def __init__(self):
        self.stats = {
            'happiness': {'value': 50, 'color': '#FFD700', 'name': 'Happiness', 'emoji': '😊'},
            'calm': {'value': 50, 'color': '#87CEEB', 'name': 'Calm', 'emoji': '😌'},
            'confidence': {'value': 50, 'color': '#FF6B6B', 'name': 'Confidence', 'emoji': '💪'},
            'focus': {'value': 50, 'color': '#4ECDC4', 'name': 'Focus', 'emoji': '🎯'},
            'energy': {'value': 50, 'color': '#45B7D1', 'name': 'Energy', 'emoji': '⚡'},
            'empathy': {'value': 50, 'color': '#96CEB4', 'name': 'Empathy', 'emoji': '❤️'}
        }
        self.level = 1
        self.score = 0
        self.moves = 30
        self.target_balance = 85
        self.achievements = {
            'first-balance': False,
            'perfectionist': False,
            'efficient': False,
            'level5': False,
            'streak': False
        }
        self.level_streak = 0
    
    def adjust_stat(self, stat_name, change):
        """Adjust a stat value and apply interactions."""
        if self.moves <= 0:
            return False
        
        if stat_name not in self.stats:
            raise ValueError(f"Invalid stat name: {stat_name}")
        
        old_value = self.stats[stat_name]['value']
        new_value = max(0, min(100, old_value + change))
        
        if old_value != new_value:
            self.stats[stat_name]['value'] = new_value
            self.moves -= 1
            self.apply_stat_interactions(stat_name, change)
            return True
        
        return False
    
    def apply_stat_interactions(self, changed_stat, change):
        """Apply stat interactions based on the changed stat."""
        interactions = {
            'happiness': {'calm': 0.3, 'confidence': 0.2, 'energy': 0.4},
            'calm': {'happiness': 0.2, 'focus': 0.5, 'confidence': 0.1},
            'confidence': {'happiness': 0.3, 'energy': 0.2, 'empathy': -0.1},
            'focus': {'calm': 0.3, 'energy': -0.2, 'empathy': -0.1},
            'energy': {'happiness': 0.2, 'confidence': 0.3, 'calm': -0.3},
            'empathy': {'happiness': 0.2, 'calm': 0.3, 'confidence': -0.1}
        }
        
        relations = interactions.get(changed_stat, {})
        
        for target_stat, multiplier in relations.items():
            if target_stat in self.stats:
                effect = change * multiplier
                current_value = self.stats[target_stat]['value']
                new_value = max(0, min(100, current_value + effect))
                self.stats[target_stat]['value'] = new_value
    
    def calculate_balance(self):
        """Calculate the current balance percentage."""
        values = [stat['value'] for stat in self.stats.values()]
        avg = sum(values) / len(values)
        variance = sum((val - avg) ** 2 for val in values) / len(values)
        balance = max(0, 100 - (variance ** 0.5))
        return round(balance)
    
    def is_level_complete(self):
        """Check if the current level is complete."""
        return self.calculate_balance() >= self.target_balance
    
    def next_level(self):
        """Advance to the next level."""
        if self.is_level_complete():
            self.level += 1
            self.target_balance = min(95, 80 + self.level * 2)
            self.moves = max(15, 35 - self.level)
            self.level_streak += 1
            self.reset_stats()
            return True
        return False
    
    def reset_stats(self):
        """Reset all stats to starting values with some randomization."""
        import random
        random_factor = 20 if self.level > 3 else 10
        
        for stat in self.stats.values():
            base_value = 50 + (random.random() - 0.5) * random_factor
            stat['value'] = max(20, min(80, round(base_value)))
    
    def reset_game(self):
        """Reset the entire game to initial state."""
        self.__init__()
    
    def check_achievements(self, balance):
        """Check and unlock achievements based on game state."""
        unlocked = []
        
        if balance >= self.target_balance and not self.achievements['first-balance']:
            self.achievements['first-balance'] = True
            unlocked.append('first-balance')
        
        if balance == 100 and not self.achievements['perfectionist']:
            self.achievements['perfectionist'] = True
            unlocked.append('perfectionist')
        
        if self.moves > 10 and balance >= self.target_balance and not self.achievements['efficient']:
            self.achievements['efficient'] = True
            unlocked.append('efficient')
        
        if self.level >= 5 and not self.achievements['level5']:
            self.achievements['level5'] = True
            unlocked.append('level5')
        
        if self.level_streak >= 5 and not self.achievements['streak']:
            self.achievements['streak'] = True
            unlocked.append('streak')
        
        return unlocked

class TestEmotionalBalanceGame(unittest.TestCase):
    """Test cases for the Emotional Balance Game."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.game = MockEmotionalBalanceGame()
    
    def test_game_initialization(self):
        """Test that the game initializes correctly."""
        self.assertEqual(self.game.level, 1)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.moves, 30)
        self.assertEqual(self.game.target_balance, 85)
        self.assertEqual(len(self.game.stats), 6)
        
        # Check initial stat values
        for stat_name, stat_data in self.game.stats.items():
            self.assertEqual(stat_data['value'], 50)
            self.assertIn('name', stat_data)
            self.assertIn('color', stat_data)
            self.assertIn('emoji', stat_data)
    
    def test_stat_adjustment(self):
        """Test stat value adjustments."""
        initial_happiness = self.game.stats['happiness']['value']
        initial_moves = self.game.moves
        
        # Test positive adjustment
        result = self.game.adjust_stat('happiness', 10)
        self.assertTrue(result)
        self.assertEqual(self.game.stats['happiness']['value'], initial_happiness + 10)
        self.assertEqual(self.game.moves, initial_moves - 1)
        
        # Test negative adjustment
        result = self.game.adjust_stat('happiness', -5)
        self.assertTrue(result)
        self.assertEqual(self.game.stats['happiness']['value'], initial_happiness + 5)
        
        # Test boundary conditions
        self.game.stats['happiness']['value'] = 95
        self.game.adjust_stat('happiness', 10)
        self.assertEqual(self.game.stats['happiness']['value'], 100)  # Should cap at 100
        
        self.game.stats['happiness']['value'] = 5
        self.game.adjust_stat('happiness', -10)
        self.assertEqual(self.game.stats['happiness']['value'], 0)  # Should not go below 0
    
    def test_stat_interactions(self):
        """Test that stat interactions work correctly."""
        # Reset to known state
        for stat in self.game.stats.values():
            stat['value'] = 50
        
        initial_calm = self.game.stats['calm']['value']
        initial_energy = self.game.stats['energy']['value']
        
        # Increase happiness, should affect calm and energy
        self.game.adjust_stat('happiness', 10)
        
        # Calm should increase (happiness -> calm: 0.3 multiplier)
        self.assertGreater(self.game.stats['calm']['value'], initial_calm)
        
        # Energy should increase (happiness -> energy: 0.4 multiplier)
        self.assertGreater(self.game.stats['energy']['value'], initial_energy)
    
    def test_balance_calculation(self):
        """Test balance calculation algorithm."""
        # All stats equal should give perfect balance
        for stat in self.game.stats.values():
            stat['value'] = 50
        balance = self.game.calculate_balance()
        self.assertEqual(balance, 100)
        
        # High variance should give lower balance
        values = [10, 90, 10, 90, 10, 90]
        for i, stat in enumerate(self.game.stats.values()):
            stat['value'] = values[i]
        balance = self.game.calculate_balance()
        self.assertLess(balance, 50)
    
    def test_level_completion(self):
        """Test level completion logic."""
        # Set balance below target
        for stat in self.game.stats.values():
            stat['value'] = 30  # This should give low balance
        self.assertFalse(self.game.is_level_complete())
        
        # Set balance above target
        for stat in self.game.stats.values():
            stat['value'] = 50  # Perfect balance
        self.assertTrue(self.game.is_level_complete())
    
    def test_next_level_progression(self):
        """Test level progression mechanics."""
        initial_level = self.game.level
        initial_target = self.game.target_balance
        
        # Set up level completion condition
        for stat in self.game.stats.values():
            stat['value'] = 50
        
        result = self.game.next_level()
        self.assertTrue(result)
        self.assertEqual(self.game.level, initial_level + 1)
        self.assertGreater(self.game.target_balance, initial_target)
        self.assertEqual(self.game.level_streak, 1)
        
        # Test that moves decrease as level increases
        self.assertLess(self.game.moves, 30)
    
    def test_moves_limit(self):
        """Test that game respects move limits."""
        self.game.moves = 1
        
        # Make one move
        result = self.game.adjust_stat('happiness', 5)
        self.assertTrue(result)
        self.assertEqual(self.game.moves, 0)
        
        # Try to make another move - should fail
        result = self.game.adjust_stat('happiness', 5)
        self.assertFalse(result)
        self.assertEqual(self.game.moves, 0)
    
    def test_invalid_stat_name(self):
        """Test handling of invalid stat names."""
        with self.assertRaises(ValueError):
            self.game.adjust_stat('invalid_stat', 10)
    
    def test_achievement_unlocking(self):
        """Test achievement unlocking system."""
        # Test first balance achievement
        balance = 85
        unlocked = self.game.check_achievements(balance)
        self.assertIn('first-balance', unlocked)
        self.assertTrue(self.game.achievements['first-balance'])
        
        # Test perfectionist achievement
        balance = 100
        unlocked = self.game.check_achievements(balance)
        self.assertIn('perfectionist', unlocked)
        self.assertTrue(self.game.achievements['perfectionist'])
        
        # Test efficient achievement
        self.game.moves = 15
        balance = 85
        unlocked = self.game.check_achievements(balance)
        self.assertIn('efficient', unlocked)
        
        # Test level 5 achievement
        self.game.level = 5
        unlocked = self.game.check_achievements(85)
        self.assertIn('level5', unlocked)
        
        # Test streak achievement
        self.game.level_streak = 5
        unlocked = self.game.check_achievements(85)
        self.assertIn('streak', unlocked)
    
    def test_game_reset(self):
        """Test game reset functionality."""
        # Modify game state
        self.game.level = 5
        self.game.score = 1000
        self.game.moves = 10
        self.game.achievements['first-balance'] = True
        
        # Reset game
        self.game.reset_game()
        
        # Check that everything is back to initial state
        self.assertEqual(self.game.level, 1)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.moves, 30)
        self.assertFalse(self.game.achievements['first-balance'])
    
    def test_stat_boundary_enforcement(self):
        """Test that stats stay within valid ranges."""
        # Test upper boundary
        self.game.stats['happiness']['value'] = 100
        self.game.adjust_stat('happiness', 10)
        self.assertEqual(self.game.stats['happiness']['value'], 100)
        
        # Test lower boundary
        self.game.stats['happiness']['value'] = 0
        self.game.adjust_stat('happiness', -10)
        self.assertEqual(self.game.stats['happiness']['value'], 0)
    
    def test_level_scaling(self):
        """Test that difficulty scales properly with levels."""
        initial_target = self.game.target_balance
        initial_moves = self.game.moves
        
        # Simulate progression through multiple levels
        for level in range(1, 6):
            self.game.level = level
            self.game.target_balance = min(95, 80 + level * 2)
            self.game.moves = max(15, 35 - level)
            
            # Target should increase
            if level > 1:
                self.assertGreaterEqual(self.game.target_balance, initial_target)
            
            # Moves should decrease (up to minimum of 15)
            if level > 1:
                self.assertLessEqual(self.game.moves, initial_moves)


class TestGameIntegration(unittest.TestCase):
    """Integration tests for game features."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.game = MockEmotionalBalanceGame()
    
    def test_complete_gameplay_scenario(self):
        """Test a complete gameplay scenario."""
        # Start game
        self.assertEqual(self.game.level, 1)
        self.assertEqual(self.game.moves, 30)
        
        # Make strategic moves to balance stats
        moves_made = 0
        while not self.game.is_level_complete() and self.game.moves > 0:
            # Simple strategy: adjust the most extreme stats toward 50
            for stat_name, stat_data in self.game.stats.items():
                if stat_data['value'] > 60:
                    self.game.adjust_stat(stat_name, -2)
                    moves_made += 1
                    break
                elif stat_data['value'] < 40:
                    self.game.adjust_stat(stat_name, 2)
                    moves_made += 1
                    break
            else:
                # If no extreme stats, make small random adjustments
                import random
                stat_name = random.choice(list(self.game.stats.keys()))
                change = random.choice([-1, 1])
                self.game.adjust_stat(stat_name, change)
                moves_made += 1
        
        # Check results
        if self.game.is_level_complete():
            balance = self.game.calculate_balance()
            self.assertGreaterEqual(balance, self.game.target_balance)
            
            # Test level progression
            initial_level = self.game.level
            self.game.next_level()
            self.assertEqual(self.game.level, initial_level + 1)
    
    def test_achievement_progression(self):
        """Test achievement unlocking through gameplay."""
        # Simulate achieving perfect balance
        for stat in self.game.stats.values():
            stat['value'] = 50
        
        balance = self.game.calculate_balance()
        unlocked = self.game.check_achievements(balance)
        
        self.assertIn('first-balance', unlocked)
        if balance == 100:
            self.assertIn('perfectionist', unlocked)
    
    def test_multi_level_progression(self):
        """Test progression through multiple levels."""
        completed_levels = 0
        max_levels = 5
        
        while completed_levels < max_levels:
            # Set perfect balance to complete level
            for stat in self.game.stats.values():
                stat['value'] = 50
            
            if self.game.is_level_complete():
                self.game.next_level()
                completed_levels += 1
            else:
                break
        
        self.assertGreater(completed_levels, 0)
        self.assertEqual(self.game.level_streak, completed_levels)


class TestGamePerformance(unittest.TestCase):
    """Performance tests for game operations."""
    
    def test_stat_adjustment_performance(self):
        """Test that stat adjustments perform efficiently."""
        import time
        
        game = MockEmotionalBalanceGame()
        
        start_time = time.time()
        
        # Perform many stat adjustments
        for _ in range(1000):
            game.adjust_stat('happiness', 1)
            if game.moves <= 0:
                game.moves = 30  # Reset moves for continued testing
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 1000 adjustments in less than 1 second
        self.assertLess(duration, 1.0)
    
    def test_balance_calculation_performance(self):
        """Test that balance calculations are efficient."""
        import time
        
        game = MockEmotionalBalanceGame()
        
        start_time = time.time()
        
        # Perform many balance calculations
        for _ in range(10000):
            game.calculate_balance()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete 10000 calculations in less than 1 second
        self.assertLess(duration, 1.0)


if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestEmotionalBalanceGame))
    suite.addTests(loader.loadTestsFromTestCase(TestGameIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestGamePerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    print("="*60)
    print("FEELSYNC GAMES TEST SUITE")
    print("="*60)
    print(f"Testing Emotional Balance Game functionality...")
    print(f"Test started at: {datetime.now()}")
    print("="*60)
    
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    print(f"\nTest completed at: {datetime.now()}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)
